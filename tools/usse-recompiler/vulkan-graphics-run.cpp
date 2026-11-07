// Headless Vulkan graphics runner for generated BMW shader-stage modules.
// It rasterizes into an RGBA8 image and writes the result as a BMP file.
#include <vulkan/vulkan.h>
#include <fstream>
#include <iostream>
#include <stdexcept>

static void check(VkResult r, const char *what) {
    if (r != VK_SUCCESS) throw std::runtime_error(std::string(what) + ": VkResult " + std::to_string(r));
}
#define VK_OK(expr) check((expr), #expr)

static std::vector<uint8_t> readFile(const char *path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) throw std::runtime_error(std::string("Cannot read ") + path);
    return {std::istreambuf_iterator<char>(in), {}};
}

static std::vector<uint32_t> shaderWords(const char *path) {
    auto bytes = readFile(path);
    if (bytes.empty() || bytes.size() % 4 || bytes.size() > 1024 * 1024)
        throw std::runtime_error(std::string("Invalid SPIR-V byte length: ") + path);
    std::vector<uint32_t> words(bytes.size() / 4);
    std::memcpy(words.data(), bytes.data(), bytes.size());
    if (words[0] != 0x07230203) throw std::runtime_error(std::string("Invalid SPIR-V magic: ") + path);
    return words;
}

struct Buffer {
    VkBuffer handle{};
    VkDeviceMemory memory{};
    VkDeviceSize allocation_size{};
    void *mapped{};
    bool coherent{};
};

struct Image {
    VkImage handle{};
    VkDeviceMemory memory{};
    VkImageView view{};
};

struct Resources {
    VkInstance instance{};
    VkPhysicalDevice physical{};
    VkDevice device{};
    VkQueue queue{};
    uint32_t queue_family{};
    VkDescriptorSetLayout descriptor_layout{};
    VkDescriptorPool descriptor_pool{};
    VkDescriptorSet descriptor_set{};
    VkPipelineCache pipeline_cache{};
    VkPipelineLayout pipeline_layout{};
    VkRenderPass render_pass{};
    VkFramebuffer framebuffer{};
    VkPipeline pipeline{};
    VkShaderModule vertex_shader{};
    VkShaderModule fragment_shader{};
    VkSampler sampler{};
    VkCommandPool command_pool{};
    VkCommandBuffer command_buffer{};
    Buffer vertex_buffer;
    Buffer uniform_buffer;
    Buffer fragment_uniform_buffer;
    Buffer texture_staging;
    Buffer readback;
    Image texture;
    Image target;

    ~Resources() {
        if (device) {
            vkDeviceWaitIdle(device);
            if (command_pool) vkDestroyCommandPool(device, command_pool, nullptr);
            if (pipeline) vkDestroyPipeline(device, pipeline, nullptr);
            if (pipeline_cache) vkDestroyPipelineCache(device, pipeline_cache, nullptr);
            if (vertex_shader) vkDestroyShaderModule(device, vertex_shader, nullptr);
            if (fragment_shader) vkDestroyShaderModule(device, fragment_shader, nullptr);
            if (pipeline_layout) vkDestroyPipelineLayout(device, pipeline_layout, nullptr);
            if (framebuffer) vkDestroyFramebuffer(device, framebuffer, nullptr);
            if (render_pass) vkDestroyRenderPass(device, render_pass, nullptr);
            if (descriptor_pool) vkDestroyDescriptorPool(device, descriptor_pool, nullptr);
            if (descriptor_layout) vkDestroyDescriptorSetLayout(device, descriptor_layout, nullptr);
            if (sampler) vkDestroySampler(device, sampler, nullptr);
            destroyImage(target);
            destroyImage(texture);
            destroyBuffer(readback);
            destroyBuffer(texture_staging);
            destroyBuffer(uniform_buffer);
            destroyBuffer(fragment_uniform_buffer);
            destroyBuffer(vertex_buffer);
            vkDestroyDevice(device, nullptr);
        }
        if (instance) vkDestroyInstance(instance, nullptr);
    }

    void destroyBuffer(Buffer &b) {
        if (b.mapped) vkUnmapMemory(device, b.memory);
        if (b.handle) vkDestroyBuffer(device, b.handle, nullptr);
        if (b.memory) vkFreeMemory(device, b.memory, nullptr);
        b = {};
    }

    void destroyImage(Image &i) {
        if (i.view) vkDestroyImageView(device, i.view, nullptr);
        if (i.handle) vkDestroyImage(device, i.handle, nullptr);
        if (i.memory) vkFreeMemory(device, i.memory, nullptr);
        i = {};
    }

    uint32_t memoryType(uint32_t bits, VkMemoryPropertyFlags required,
                        VkMemoryPropertyFlags preferred, VkMemoryPropertyFlags *chosen = nullptr) {
        VkPhysicalDeviceMemoryProperties properties{};
        vkGetPhysicalDeviceMemoryProperties(physical, &properties);
        uint32_t fallback = UINT32_MAX;
        for (uint32_t i = 0; i < properties.memoryTypeCount; ++i) {
            if (!(bits & (1u << i))) continue;
            VkMemoryPropertyFlags flags = properties.memoryTypes[i].propertyFlags;
            if ((flags & required) != required) continue;
            if (fallback == UINT32_MAX) fallback = i;
            if ((flags & preferred) == preferred) {
                if (chosen) *chosen = flags;
                return i;
            }
        }
        if (fallback == UINT32_MAX) throw std::runtime_error("No compatible Vulkan memory type");
        if (chosen) *chosen = properties.memoryTypes[fallback].propertyFlags;
        return fallback;
    }

    Buffer makeBuffer(VkDeviceSize size, VkBufferUsageFlags usage, bool host_visible) {
        Buffer result{};
        VkBufferCreateInfo info{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};
        info.size = size;
        info.usage = usage;
        info.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        VK_OK(vkCreateBuffer(device, &info, nullptr, &result.handle));
        VkMemoryRequirements requirements{};
        vkGetBufferMemoryRequirements(device, result.handle, &requirements);
        VkMemoryPropertyFlags flags{};
        uint32_t type = memoryType(requirements.memoryTypeBits,
            host_visible ? VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT : 0,
            host_visible ? VK_MEMORY_PROPERTY_HOST_COHERENT_BIT : VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
            &flags);
        VkMemoryAllocateInfo allocation{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};
        allocation.allocationSize = requirements.size;
        allocation.memoryTypeIndex = type;
        VK_OK(vkAllocateMemory(device, &allocation, nullptr, &result.memory));
        result.allocation_size = requirements.size;
        result.coherent = (flags & VK_MEMORY_PROPERTY_HOST_COHERENT_BIT) != 0;
        VK_OK(vkBindBufferMemory(device, result.handle, result.memory, 0));
        if (host_visible) VK_OK(vkMapMemory(device, result.memory, 0, VK_WHOLE_SIZE, 0, &result.mapped));
        return result;
    }

    void flush(const Buffer &b) {
        if (b.coherent) return;
        VkMappedMemoryRange range{VK_STRUCTURE_TYPE_MAPPED_MEMORY_RANGE};
        range.memory = b.memory;
        range.size = VK_WHOLE_SIZE;
        VK_OK(vkFlushMappedMemoryRanges(device, 1, &range));
    }

    void invalidate(const Buffer &b) {
        if (b.coherent) return;
        VkMappedMemoryRange range{VK_STRUCTURE_TYPE_MAPPED_MEMORY_RANGE};
        range.memory = b.memory;
        range.size = VK_WHOLE_SIZE;
        VK_OK(vkInvalidateMappedMemoryRanges(device, 1, &range));
    }

    Image makeImage(uint32_t width, uint32_t height, VkImageUsageFlags usage) {
        Image result{};
        VkImageCreateInfo info{VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO};
        info.imageType = VK_IMAGE_TYPE_2D;
        info.format = VK_FORMAT_R8G8B8A8_UNORM;
        info.extent = {width, height, 1};
        info.mipLevels = 1;
        info.arrayLayers = 1;
        info.samples = VK_SAMPLE_COUNT_1_BIT;
        info.tiling = VK_IMAGE_TILING_OPTIMAL;
        info.usage = usage;
        info.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        info.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
        VK_OK(vkCreateImage(device, &info, nullptr, &result.handle));
        VkMemoryRequirements requirements{};
        vkGetImageMemoryRequirements(device, result.handle, &requirements);
        VkMemoryPropertyFlags flags{};
        uint32_t type = memoryType(requirements.memoryTypeBits, 0, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT, &flags);
        VkMemoryAllocateInfo allocation{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};
        allocation.allocationSize = requirements.size;
        allocation.memoryTypeIndex = type;
        VK_OK(vkAllocateMemory(device, &allocation, nullptr, &result.memory));
        VK_OK(vkBindImageMemory(device, result.handle, result.memory, 0));
        VkImageViewCreateInfo view{VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO};
        view.image = result.handle;
        view.viewType = VK_IMAGE_VIEW_TYPE_2D;
        view.format = VK_FORMAT_R8G8B8A8_UNORM;
        view.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
        VK_OK(vkCreateImageView(device, &view, nullptr, &result.view));
        return result;
    }
};

static void writeBmp(const char *path, const uint8_t *rgba, uint32_t width, uint32_t height) {
    const uint32_t image_size = width * height * 4;
    std::ofstream out(path, std::ios::binary);
    if (!out) throw std::runtime_error(std::string("Cannot write ") + path);
    uint8_t header[54]{};
    header[0] = 'B'; header[1] = 'M';
    auto put32 = [&](int offset, uint32_t value) {
        header[offset] = value & 0xff;
        header[offset + 1] = (value >> 8) & 0xff;
        header[offset + 2] = (value >> 16) & 0xff;
        header[offset + 3] = (value >> 24) & 0xff;
    };
    header[2] = (54 + image_size) & 0xff;
    header[3] = ((54 + image_size) >> 8) & 0xff;
    header[4] = ((54 + image_size) >> 16) & 0xff;
    header[5] = ((54 + image_size) >> 24) & 0xff;
    put32(10, 54); put32(14, 40); put32(18, width); put32(22, height);
    header[26] = 1; header[28] = 32;
    put32(34, image_size);
    out.write(reinterpret_cast<const char *>(header), sizeof(header));
    std::vector<uint8_t> row(width * 4);
    for (uint32_t y = height; y-- > 0;) {
        for (uint32_t x = 0; x < width; ++x) {
            const uint8_t *p = rgba + (size_t(y) * width + x) * 4;
            row[x * 4 + 0] = p[2]; row[x * 4 + 1] = p[1];
            row[x * 4 + 2] = p[0]; row[x * 4 + 3] = p[3];
        }
        out.write(reinterpret_cast<const char *>(row.data()), row.size());
    }
    if (!out) throw std::runtime_error("Failed while writing BMP output");
}

int main(int argc, char **argv) try {
    if (argc != 9 && argc != 11)
        throw std::runtime_error("Usage: idrive-vulkan-graphics VERTEX.spv FRAGMENT.spv VERTEX_UNIFORMS.bin FRAGMENT_UNIFORMS.bin TEXTURE.rgba TEX_WIDTH TEX_HEIGHT OUTPUT.bmp [PIPELINE_CACHE_IN|- PIPELINE_CACHE_OUT|-]");
    const uint32_t tex_width = std::stoul(argv[6]), tex_height = std::stoul(argv[7]);
    if (!tex_width || !tex_height || tex_width > 4096 || tex_height > 4096)
        throw std::runtime_error("Texture dimensions must be 1..4096");
    auto vertex_words = shaderWords(argv[1]);
    auto fragment_words = shaderWords(argv[2]);
    auto vertex_uniforms = readFile(argv[3]);
    auto fragment_uniforms = readFile(argv[4]);
    auto texture = readFile(argv[5]);
    std::vector<uint8_t> pipeline_cache_input;
    const bool load_pipeline_cache = argc == 11 && std::string(argv[9]) != "-";
    const bool save_pipeline_cache = argc == 11 && std::string(argv[10]) != "-";
    if (load_pipeline_cache) pipeline_cache_input = readFile(argv[9]);
    if (vertex_uniforms.size() != 32 * 16 || fragment_uniforms.size() != 32 * 16 ||
        texture.size() != size_t(tex_width) * tex_height * 4)
        throw std::runtime_error("Expected two 32-vec4 uniform banks and tightly packed RGBA8 texture data");
    constexpr uint32_t width = 256, height = 256;
    struct Vertex { float x, y, z, w, u, v; };
    const Vertex vertices[] = {
        {-1, -1, 0, 1, 0, 1}, { 1, -1, 0, 1, 1, 1}, { 1,  1, 0, 1, 1, 0},
        {-1, -1, 0, 1, 0, 1}, { 1,  1, 0, 1, 1, 0}, {-1,  1, 0, 1, 0, 0},
    };

    Resources r;
    uint32_t count = 0;
    VK_OK(vkEnumerateInstanceExtensionProperties(nullptr, &count, nullptr));
    std::vector<VkExtensionProperties> extensions(count);
    VK_OK(vkEnumerateInstanceExtensionProperties(nullptr, &count, extensions.data()));
    std::vector<const char *> instance_extensions;
    for (const auto &e : extensions)
        if (std::string(e.extensionName) == VK_KHR_PORTABILITY_ENUMERATION_EXTENSION_NAME)
            instance_extensions.push_back(VK_KHR_PORTABILITY_ENUMERATION_EXTENSION_NAME);
    VkApplicationInfo app{VK_STRUCTURE_TYPE_APPLICATION_INFO};
    app.pApplicationName = "BMW genuine shader offscreen draw";
    app.apiVersion = VK_API_VERSION_1_0;
    VkInstanceCreateInfo instance_info{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};
    instance_info.pApplicationInfo = &app;
    instance_info.enabledExtensionCount = instance_extensions.size();
    instance_info.ppEnabledExtensionNames = instance_extensions.data();
    if (!instance_extensions.empty()) instance_info.flags = VK_INSTANCE_CREATE_ENUMERATE_PORTABILITY_BIT_KHR;
    VK_OK(vkCreateInstance(&instance_info, nullptr, &r.instance));
    VK_OK(vkEnumeratePhysicalDevices(r.instance, &count, nullptr));
    std::vector<VkPhysicalDevice> devices(count);
    VK_OK(vkEnumeratePhysicalDevices(r.instance, &count, devices.data()));
    for (VkPhysicalDevice physical : devices) {
        uint32_t queues_count = 0;
        vkGetPhysicalDeviceQueueFamilyProperties(physical, &queues_count, nullptr);
        std::vector<VkQueueFamilyProperties> queues(queues_count);
        vkGetPhysicalDeviceQueueFamilyProperties(physical, &queues_count, queues.data());
        for (uint32_t i = 0; i < queues_count; ++i)
            if (queues[i].queueCount && (queues[i].queueFlags & VK_QUEUE_GRAPHICS_BIT)) {
                r.physical = physical; r.queue_family = i; break;
            }
        if (r.physical) break;
    }
    if (!r.physical) throw std::runtime_error("No Vulkan graphics queue available");
    VkPhysicalDeviceProperties properties{};
    vkGetPhysicalDeviceProperties(r.physical, &properties);
    VK_OK(vkEnumerateDeviceExtensionProperties(r.physical, nullptr, &count, nullptr));
    extensions.resize(count);
    VK_OK(vkEnumerateDeviceExtensionProperties(r.physical, nullptr, &count, extensions.data()));
    std::vector<const char *> device_extensions;
    for (const auto &e : extensions)
        if (std::string(e.extensionName) == "VK_KHR_portability_subset")
            device_extensions.push_back("VK_KHR_portability_subset");
    float priority = 1;
    VkDeviceQueueCreateInfo queue_info{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};
    queue_info.queueFamilyIndex = r.queue_family; queue_info.queueCount = 1; queue_info.pQueuePriorities = &priority;
    VkDeviceCreateInfo device_info{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};
    device_info.queueCreateInfoCount = 1; device_info.pQueueCreateInfos = &queue_info;
    device_info.enabledExtensionCount = device_extensions.size(); device_info.ppEnabledExtensionNames = device_extensions.data();
    VK_OK(vkCreateDevice(r.physical, &device_info, nullptr, &r.device));
    vkGetDeviceQueue(r.device, r.queue_family, 0, &r.queue);

    r.vertex_buffer = r.makeBuffer(sizeof(vertices), VK_BUFFER_USAGE_VERTEX_BUFFER_BIT, true);
    std::memcpy(r.vertex_buffer.mapped, vertices, sizeof(vertices)); r.flush(r.vertex_buffer);
    r.uniform_buffer = r.makeBuffer(vertex_uniforms.size(), VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT, true);
    std::memcpy(r.uniform_buffer.mapped, vertex_uniforms.data(), vertex_uniforms.size());
    r.flush(r.uniform_buffer);
    r.fragment_uniform_buffer = r.makeBuffer(fragment_uniforms.size(), VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT, true);
    std::memcpy(r.fragment_uniform_buffer.mapped, fragment_uniforms.data(), fragment_uniforms.size());
    r.flush(r.fragment_uniform_buffer);
    r.texture_staging = r.makeBuffer(texture.size(), VK_BUFFER_USAGE_TRANSFER_SRC_BIT, true);
    std::memcpy(r.texture_staging.mapped, texture.data(), texture.size()); r.flush(r.texture_staging);
    r.readback = r.makeBuffer(width * height * 4, VK_BUFFER_USAGE_TRANSFER_DST_BIT, true);
    r.texture = r.makeImage(tex_width, tex_height, VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_SAMPLED_BIT);
    r.target = r.makeImage(width, height, VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT);

    VkSamplerCreateInfo sampler_info{VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO};
    sampler_info.magFilter = VK_FILTER_NEAREST; sampler_info.minFilter = VK_FILTER_NEAREST;
    sampler_info.mipmapMode = VK_SAMPLER_MIPMAP_MODE_NEAREST;
    sampler_info.addressModeU = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    sampler_info.addressModeV = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    sampler_info.addressModeW = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    sampler_info.maxLod = 0;
    VK_OK(vkCreateSampler(r.device, &sampler_info, nullptr, &r.sampler));

    VkAttachmentDescription attachment{};
    attachment.format = VK_FORMAT_R8G8B8A8_UNORM; attachment.samples = VK_SAMPLE_COUNT_1_BIT;
    attachment.loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR; attachment.storeOp = VK_ATTACHMENT_STORE_OP_STORE;
    attachment.stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE; attachment.stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
    attachment.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED; attachment.finalLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
    VkAttachmentReference color_ref{0, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL};
    VkSubpassDescription subpass{}; subpass.pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS;
    subpass.colorAttachmentCount = 1; subpass.pColorAttachments = &color_ref;
    VkSubpassDependency dependency{};
    dependency.srcSubpass = VK_SUBPASS_EXTERNAL; dependency.dstSubpass = 0;
    dependency.srcStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    dependency.dstStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    dependency.dstAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;
    VkRenderPassCreateInfo render_info{VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO};
    render_info.attachmentCount = 1; render_info.pAttachments = &attachment;
    render_info.subpassCount = 1; render_info.pSubpasses = &subpass;
    render_info.dependencyCount = 1; render_info.pDependencies = &dependency;
    VK_OK(vkCreateRenderPass(r.device, &render_info, nullptr, &r.render_pass));
    VkFramebufferCreateInfo framebuffer_info{VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO};
    framebuffer_info.renderPass = r.render_pass; framebuffer_info.attachmentCount = 1;
    framebuffer_info.pAttachments = &r.target.view; framebuffer_info.width = width; framebuffer_info.height = height; framebuffer_info.layers = 1;
    VK_OK(vkCreateFramebuffer(r.device, &framebuffer_info, nullptr, &r.framebuffer));

    VkDescriptorSetLayoutBinding bindings[3]{};
    bindings[0] = {0, VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER, 1, VK_SHADER_STAGE_VERTEX_BIT, nullptr};
    bindings[1] = {1, VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, 1, VK_SHADER_STAGE_FRAGMENT_BIT, nullptr};
    bindings[2] = {2, VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER, 1, VK_SHADER_STAGE_FRAGMENT_BIT, nullptr};
    VkDescriptorSetLayoutCreateInfo set_info{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};
    set_info.bindingCount = 3; set_info.pBindings = bindings;
    VK_OK(vkCreateDescriptorSetLayout(r.device, &set_info, nullptr, &r.descriptor_layout));
    VkDescriptorPoolSize pool_sizes[2] = {{VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER, 2}, {VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, 1}};
    VkDescriptorPoolCreateInfo pool_info{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};
    pool_info.maxSets = 1; pool_info.poolSizeCount = 2; pool_info.pPoolSizes = pool_sizes;
    VK_OK(vkCreateDescriptorPool(r.device, &pool_info, nullptr, &r.descriptor_pool));
    VkDescriptorSetAllocateInfo set_alloc{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};
    set_alloc.descriptorPool = r.descriptor_pool; set_alloc.descriptorSetCount = 1; set_alloc.pSetLayouts = &r.descriptor_layout;
    VK_OK(vkAllocateDescriptorSets(r.device, &set_alloc, &r.descriptor_set));
    VkDescriptorBufferInfo vertex_uniform_info{r.uniform_buffer.handle, 0, vertex_uniforms.size()};
    VkDescriptorBufferInfo fragment_uniform_info{r.fragment_uniform_buffer.handle, 0, fragment_uniforms.size()};
    VkDescriptorImageInfo texture_info{r.sampler, r.texture.view, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};
    VkWriteDescriptorSet writes[3]{};
    writes[0] = {VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET}; writes[0].dstSet = r.descriptor_set; writes[0].dstBinding = 0;
    writes[0].descriptorCount = 1; writes[0].descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER; writes[0].pBufferInfo = &vertex_uniform_info;
    writes[1] = {VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET}; writes[1].dstSet = r.descriptor_set; writes[1].dstBinding = 1;
    writes[1].descriptorCount = 1; writes[1].descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER; writes[1].pImageInfo = &texture_info;
    writes[2] = {VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET}; writes[2].dstSet = r.descriptor_set; writes[2].dstBinding = 2;
    writes[2].descriptorCount = 1; writes[2].descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER; writes[2].pBufferInfo = &fragment_uniform_info;
    vkUpdateDescriptorSets(r.device, 3, writes, 0, nullptr);
    VkPipelineLayoutCreateInfo layout_info{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};
    layout_info.setLayoutCount = 1; layout_info.pSetLayouts = &r.descriptor_layout;
    VK_OK(vkCreatePipelineLayout(r.device, &layout_info, nullptr, &r.pipeline_layout));

    VkShaderModuleCreateInfo module_info{VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO};
    module_info.codeSize = vertex_words.size() * 4; module_info.pCode = vertex_words.data();
    VK_OK(vkCreateShaderModule(r.device, &module_info, nullptr, &r.vertex_shader));
    module_info.codeSize = fragment_words.size() * 4; module_info.pCode = fragment_words.data();
    VK_OK(vkCreateShaderModule(r.device, &module_info, nullptr, &r.fragment_shader));
    VkPipelineShaderStageCreateInfo stages[2]{};
    stages[0] = {VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO}; stages[0].stage = VK_SHADER_STAGE_VERTEX_BIT;
    stages[0].module = r.vertex_shader; stages[0].pName = "main";
    stages[1] = {VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO}; stages[1].stage = VK_SHADER_STAGE_FRAGMENT_BIT;
    stages[1].module = r.fragment_shader; stages[1].pName = "main";
    VkVertexInputBindingDescription vertex_binding{0, sizeof(Vertex), VK_VERTEX_INPUT_RATE_VERTEX};
    VkVertexInputAttributeDescription attributes[2] = {
        {0, 0, VK_FORMAT_R32G32B32A32_SFLOAT, offsetof(Vertex, x)},
        {1, 0, VK_FORMAT_R32G32_SFLOAT, offsetof(Vertex, u)},
    };
    VkPipelineVertexInputStateCreateInfo vertex_input{VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO};
    vertex_input.vertexBindingDescriptionCount = 1; vertex_input.pVertexBindingDescriptions = &vertex_binding;
    vertex_input.vertexAttributeDescriptionCount = 2; vertex_input.pVertexAttributeDescriptions = attributes;
    VkPipelineInputAssemblyStateCreateInfo assembly{VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO};
    assembly.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;
    VkPipelineViewportStateCreateInfo viewport{VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO};
    viewport.viewportCount = 1; viewport.scissorCount = 1;
    VkPipelineRasterizationStateCreateInfo raster{VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO};
    raster.polygonMode = VK_POLYGON_MODE_FILL; raster.cullMode = VK_CULL_MODE_NONE;
    raster.frontFace = VK_FRONT_FACE_COUNTER_CLOCKWISE; raster.lineWidth = 1.0f;
    VkPipelineMultisampleStateCreateInfo multisample{VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO};
    multisample.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;
    VkPipelineColorBlendAttachmentState blend_attachment{}; blend_attachment.colorWriteMask = 0xf;
    VkPipelineColorBlendStateCreateInfo blend{VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO};
    blend.attachmentCount = 1; blend.pAttachments = &blend_attachment;
    VkDynamicState dynamic_states[] = {VK_DYNAMIC_STATE_VIEWPORT, VK_DYNAMIC_STATE_SCISSOR};
    VkPipelineDynamicStateCreateInfo dynamic{VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO};
    dynamic.dynamicStateCount = 2; dynamic.pDynamicStates = dynamic_states;
    VkGraphicsPipelineCreateInfo pipeline_info{VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO};
    pipeline_info.stageCount = 2; pipeline_info.pStages = stages; pipeline_info.pVertexInputState = &vertex_input;
    pipeline_info.pInputAssemblyState = &assembly; pipeline_info.pViewportState = &viewport;
    pipeline_info.pRasterizationState = &raster; pipeline_info.pMultisampleState = &multisample;
    pipeline_info.pColorBlendState = &blend; pipeline_info.pDynamicState = &dynamic;
    pipeline_info.layout = r.pipeline_layout; pipeline_info.renderPass = r.render_pass; pipeline_info.subpass = 0;
    VkPipelineCacheCreateInfo pipeline_cache_info{VK_STRUCTURE_TYPE_PIPELINE_CACHE_CREATE_INFO};
    pipeline_cache_info.initialDataSize = pipeline_cache_input.size();
    pipeline_cache_info.pInitialData = pipeline_cache_input.empty() ? nullptr : pipeline_cache_input.data();
    VK_OK(vkCreatePipelineCache(r.device, &pipeline_cache_info, nullptr, &r.pipeline_cache));
    VK_OK(vkCreateGraphicsPipelines(r.device, r.pipeline_cache, 1, &pipeline_info, nullptr, &r.pipeline));
    if (save_pipeline_cache) {
        size_t size = 0;
        VK_OK(vkGetPipelineCacheData(r.device, r.pipeline_cache, &size, nullptr));
        std::vector<uint8_t> data(size);
        VkResult cache_result = vkGetPipelineCacheData(r.device, r.pipeline_cache, &size, data.data());
        if (cache_result != VK_SUCCESS && cache_result != VK_INCOMPLETE)
            check(cache_result, "vkGetPipelineCacheData");
        data.resize(size);
        std::ofstream cache_out(argv[10], std::ios::binary);
        cache_out.write(reinterpret_cast<const char *>(data.data()), data.size());
        if (!cache_out) throw std::runtime_error("Failed while writing Vulkan pipeline cache");
    }

    VkCommandPoolCreateInfo command_pool_info{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};
    command_pool_info.queueFamilyIndex = r.queue_family;
    VK_OK(vkCreateCommandPool(r.device, &command_pool_info, nullptr, &r.command_pool));
    VkCommandBufferAllocateInfo command_alloc{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};
    command_alloc.commandPool = r.command_pool; command_alloc.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY; command_alloc.commandBufferCount = 1;
    VK_OK(vkAllocateCommandBuffers(r.device, &command_alloc, &r.command_buffer));
    VkCommandBufferBeginInfo begin{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
    begin.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    VK_OK(vkBeginCommandBuffer(r.command_buffer, &begin));
    VkImageMemoryBarrier texture_barrier{VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER};
    texture_barrier.srcAccessMask = 0; texture_barrier.dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
    texture_barrier.oldLayout = VK_IMAGE_LAYOUT_UNDEFINED; texture_barrier.newLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
    texture_barrier.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED; texture_barrier.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    texture_barrier.image = r.texture.handle; texture_barrier.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    vkCmdPipelineBarrier(r.command_buffer, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, 0, 0, nullptr, 0, nullptr, 1, &texture_barrier);
    VkBufferImageCopy texture_copy{}; texture_copy.imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
    texture_copy.imageExtent = {tex_width, tex_height, 1};
    vkCmdCopyBufferToImage(r.command_buffer, r.texture_staging.handle, r.texture.handle, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &texture_copy);
    texture_barrier.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT; texture_barrier.dstAccessMask = VK_ACCESS_SHADER_READ_BIT;
    texture_barrier.oldLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL; texture_barrier.newLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
    vkCmdPipelineBarrier(r.command_buffer, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, 0, 0, nullptr, 0, nullptr, 1, &texture_barrier);
    VkClearValue clear{}; clear.color = {{0, 0, 0, 0}};
    VkRenderPassBeginInfo pass{VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO};
    pass.renderPass = r.render_pass; pass.framebuffer = r.framebuffer; pass.renderArea = {{0, 0}, {width, height}};
    pass.clearValueCount = 1; pass.pClearValues = &clear;
    vkCmdBeginRenderPass(r.command_buffer, &pass, VK_SUBPASS_CONTENTS_INLINE);
    vkCmdBindPipeline(r.command_buffer, VK_PIPELINE_BIND_POINT_GRAPHICS, r.pipeline);
    vkCmdBindDescriptorSets(r.command_buffer, VK_PIPELINE_BIND_POINT_GRAPHICS, r.pipeline_layout, 0, 1, &r.descriptor_set, 0, nullptr);
    VkViewport vk_viewport{0, 0, float(width), float(height), 0, 1};
    VkRect2D scissor{{0, 0}, {width, height}};
    vkCmdSetViewport(r.command_buffer, 0, 1, &vk_viewport); vkCmdSetScissor(r.command_buffer, 0, 1, &scissor);
    VkDeviceSize vertex_offset = 0;
    vkCmdBindVertexBuffers(r.command_buffer, 0, 1, &r.vertex_buffer.handle, &vertex_offset);
    vkCmdDraw(r.command_buffer, 6, 1, 0, 0);
    vkCmdEndRenderPass(r.command_buffer);
    VkImageMemoryBarrier target_barrier{VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER};
    target_barrier.srcAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT; target_barrier.dstAccessMask = VK_ACCESS_TRANSFER_READ_BIT;
    target_barrier.oldLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL; target_barrier.newLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;
    target_barrier.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED; target_barrier.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    target_barrier.image = r.target.handle; target_barrier.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    vkCmdPipelineBarrier(r.command_buffer, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, 0, 0, nullptr, 0, nullptr, 1, &target_barrier);
    VkBufferImageCopy readback_copy{}; readback_copy.imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
    readback_copy.imageExtent = {width, height, 1};
    vkCmdCopyImageToBuffer(r.command_buffer, r.target.handle, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, r.readback.handle, 1, &readback_copy);
    VkBufferMemoryBarrier host_barrier{VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER};
    host_barrier.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT; host_barrier.dstAccessMask = VK_ACCESS_HOST_READ_BIT;
    host_barrier.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED; host_barrier.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    host_barrier.buffer = r.readback.handle; host_barrier.offset = 0; host_barrier.size = VK_WHOLE_SIZE;
    vkCmdPipelineBarrier(r.command_buffer, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_HOST_BIT, 0, 0, nullptr, 1, &host_barrier, 0, nullptr);
    VK_OK(vkEndCommandBuffer(r.command_buffer));
    VkSubmitInfo submit{VK_STRUCTURE_TYPE_SUBMIT_INFO}; submit.commandBufferCount = 1; submit.pCommandBuffers = &r.command_buffer;
    VK_OK(vkQueueSubmit(r.queue, 1, &submit, VK_NULL_HANDLE)); VK_OK(vkQueueWaitIdle(r.queue));
    r.invalidate(r.readback);
    writeBmp(argv[8], static_cast<const uint8_t *>(r.readback.mapped), width, height);
    std::cout << "Rendered 6 vertices to " << width << "x" << height << " RGBA8 on " << properties.deviceName << "\n";
} catch (const std::exception &e) {
    std::cerr << e.what() << '\n';
    return 1;
}

