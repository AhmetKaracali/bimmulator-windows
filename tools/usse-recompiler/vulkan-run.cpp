// Headless computational probe. Executes translated register arithmetic;
// it does not implement BMW textures, draw state, Screen or presentation.
#include <vulkan/vulkan.h>
#include <fstream>
#include <iostream>
#include <stdexcept>

static void check(VkResult r,const char *what) {
    if(r!=VK_SUCCESS) throw std::runtime_error(std::string(what)+": VkResult "+std::to_string(r));
}
#define VK_OK(expr) check((expr),#expr)
struct Resources {
    VkInstance instance{}; VkDevice device{}; VkBuffer buffer{};
    VkDeviceMemory memory{}; void *mapped{};
    VkDescriptorSetLayout set_layout{}; VkDescriptorPool descriptor_pool{};
    VkPipelineLayout pipeline_layout{}; VkShaderModule shader{};
    VkPipeline pipeline{}; VkCommandPool command_pool{};
    ~Resources() {
        if(device) {
            vkDeviceWaitIdle(device);
            if(command_pool) vkDestroyCommandPool(device,command_pool,nullptr);
            if(pipeline) vkDestroyPipeline(device,pipeline,nullptr);
            if(shader) vkDestroyShaderModule(device,shader,nullptr);
            if(pipeline_layout) vkDestroyPipelineLayout(device,pipeline_layout,nullptr);
            if(descriptor_pool) vkDestroyDescriptorPool(device,descriptor_pool,nullptr);
            if(set_layout) vkDestroyDescriptorSetLayout(device,set_layout,nullptr);
            if(mapped) vkUnmapMemory(device,memory);
            if(buffer) vkDestroyBuffer(device,buffer,nullptr);
            if(memory) vkFreeMemory(device,memory,nullptr);
            vkDestroyDevice(device,nullptr);
        }
        if(instance) vkDestroyInstance(instance,nullptr);
    }
};
static std::vector<uint8_t> read(const char *path) {
    std::ifstream in(path,std::ios::binary);
    if(!in) throw std::runtime_error(std::string("Cannot read ")+path);
    return {std::istreambuf_iterator<char>(in),{}};
}
int main(int argc,char **argv) try {
    if(argc!=4) throw std::runtime_error("Usage: idrive-vulkan-compute SHADER.spv STATE_IN.bin STATE_OUT.bin");
    auto shader=read(argv[1]),state=read(argv[2]);
    if(shader.empty() || shader.size()%4 || shader.size()>1024*1024 || state.size()!=132*16)
        throw std::runtime_error("Expected SPIR-V words and 132 vec4 register-state entries");
    // Preserve alignment independently of the byte-vector allocator.
    std::vector<uint32_t> words(shader.size()/4);
    std::memcpy(words.data(),shader.data(),shader.size());
    if(words[0]!=0x07230203) throw std::runtime_error("Invalid SPIR-V magic");
    Resources r;
    uint32_t count=0;
    VK_OK(vkEnumerateInstanceExtensionProperties(nullptr,&count,nullptr));
    std::vector<VkExtensionProperties> extensions(count);
    VK_OK(vkEnumerateInstanceExtensionProperties(nullptr,&count,extensions.data()));
    std::vector<const char*> instance_extensions;
    for(auto &e:extensions)
        if(std::string(e.extensionName)==VK_KHR_PORTABILITY_ENUMERATION_EXTENSION_NAME)
            instance_extensions.push_back(VK_KHR_PORTABILITY_ENUMERATION_EXTENSION_NAME);
    VkApplicationInfo app{VK_STRUCTURE_TYPE_APPLICATION_INFO};
    app.pApplicationName="BMW shader arithmetic probe"; app.apiVersion=VK_API_VERSION_1_0;
    VkInstanceCreateInfo ci{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};ci.pApplicationInfo=&app;
    ci.enabledExtensionCount=instance_extensions.size();ci.ppEnabledExtensionNames=instance_extensions.data();
    if(!instance_extensions.empty())ci.flags=VK_INSTANCE_CREATE_ENUMERATE_PORTABILITY_BIT_KHR;
    VK_OK(vkCreateInstance(&ci,nullptr,&r.instance));
    VK_OK(vkEnumeratePhysicalDevices(r.instance,&count,nullptr));
    std::vector<VkPhysicalDevice> devices(count);
    VK_OK(vkEnumeratePhysicalDevices(r.instance,&count,devices.data()));
    VkPhysicalDevice physical{}; uint32_t family=0;
    for(auto device:devices) {
        uint32_t n=0;vkGetPhysicalDeviceQueueFamilyProperties(device,&n,nullptr);
        std::vector<VkQueueFamilyProperties> queues(n);vkGetPhysicalDeviceQueueFamilyProperties(device,&n,queues.data());
        for(uint32_t i=0;i<n;i++)if(queues[i].queueCount && (queues[i].queueFlags&VK_QUEUE_COMPUTE_BIT)) {
            physical=device;family=i;break;
        }
        if(physical)break;
    }
    if(!physical)throw std::runtime_error("No Vulkan compute device available");
    VkPhysicalDeviceProperties properties;vkGetPhysicalDeviceProperties(physical,&properties);
    VK_OK(vkEnumerateDeviceExtensionProperties(physical,nullptr,&count,nullptr));
    extensions.resize(count);VK_OK(vkEnumerateDeviceExtensionProperties(physical,nullptr,&count,extensions.data()));
    std::vector<const char*> device_extensions;
    for(auto &e:extensions)if(std::string(e.extensionName)=="VK_KHR_portability_subset")device_extensions.push_back("VK_KHR_portability_subset");
    float priority=1;
    VkDeviceQueueCreateInfo qi{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};
    qi.queueFamilyIndex=family;qi.queueCount=1;qi.pQueuePriorities=&priority;
    VkDeviceCreateInfo di{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};di.queueCreateInfoCount=1;di.pQueueCreateInfos=&qi;
    di.enabledExtensionCount=device_extensions.size();di.ppEnabledExtensionNames=device_extensions.data();
    VK_OK(vkCreateDevice(physical,&di,nullptr,&r.device));
    VkQueue queue;vkGetDeviceQueue(r.device,family,0,&queue);
    VkBufferCreateInfo bi{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};bi.size=state.size();bi.usage=VK_BUFFER_USAGE_STORAGE_BUFFER_BIT;
    bi.sharingMode=VK_SHARING_MODE_EXCLUSIVE;VK_OK(vkCreateBuffer(r.device,&bi,nullptr,&r.buffer));
    VkMemoryRequirements requirements;vkGetBufferMemoryRequirements(r.device,r.buffer,&requirements);
    VkPhysicalDeviceMemoryProperties mp;vkGetPhysicalDeviceMemoryProperties(physical,&mp);
    uint32_t memory_type=UINT32_MAX;bool coherent=false;
    for(int pass=0;pass<2 && memory_type==UINT32_MAX;pass++)for(uint32_t i=0;i<mp.memoryTypeCount;i++) {
        auto flags=mp.memoryTypes[i].propertyFlags;
        if((requirements.memoryTypeBits&(1u<<i)) && (flags&VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT) &&
           (pass || (flags&VK_MEMORY_PROPERTY_HOST_COHERENT_BIT))) {
            memory_type=i;coherent=flags&VK_MEMORY_PROPERTY_HOST_COHERENT_BIT;break;
        }
    }
    if(memory_type==UINT32_MAX)throw std::runtime_error("No host-visible Vulkan buffer memory");
    VkMemoryAllocateInfo ai{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};ai.allocationSize=requirements.size;ai.memoryTypeIndex=memory_type;
    VK_OK(vkAllocateMemory(r.device,&ai,nullptr,&r.memory));VK_OK(vkBindBufferMemory(r.device,r.buffer,r.memory,0));
    VK_OK(vkMapMemory(r.device,r.memory,0,VK_WHOLE_SIZE,0,&r.mapped));std::memcpy(r.mapped,state.data(),state.size());
    VkMappedMemoryRange range{VK_STRUCTURE_TYPE_MAPPED_MEMORY_RANGE};range.memory=r.memory;range.size=VK_WHOLE_SIZE;
    if(!coherent)VK_OK(vkFlushMappedMemoryRanges(r.device,1,&range));
    VkDescriptorSetLayoutBinding binding{0,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1,VK_SHADER_STAGE_COMPUTE_BIT,nullptr};
    VkDescriptorSetLayoutCreateInfo li{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};li.bindingCount=1;li.pBindings=&binding;
    VK_OK(vkCreateDescriptorSetLayout(r.device,&li,nullptr,&r.set_layout));
    VkDescriptorPoolSize pool_size{VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1};
    VkDescriptorPoolCreateInfo pi{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};pi.maxSets=1;pi.poolSizeCount=1;pi.pPoolSizes=&pool_size;
    VK_OK(vkCreateDescriptorPool(r.device,&pi,nullptr,&r.descriptor_pool));
    VkDescriptorSetAllocateInfo sai{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};sai.descriptorPool=r.descriptor_pool;sai.descriptorSetCount=1;sai.pSetLayouts=&r.set_layout;
    VkDescriptorSet set;VK_OK(vkAllocateDescriptorSets(r.device,&sai,&set));
    VkDescriptorBufferInfo buffer_info{r.buffer,0,state.size()};
    VkWriteDescriptorSet write{VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET};write.dstSet=set;write.dstBinding=0;write.descriptorCount=1;
    write.descriptorType=VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;write.pBufferInfo=&buffer_info;vkUpdateDescriptorSets(r.device,1,&write,0,nullptr);
    VkPipelineLayoutCreateInfo pli{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};pli.setLayoutCount=1;pli.pSetLayouts=&r.set_layout;
    VK_OK(vkCreatePipelineLayout(r.device,&pli,nullptr,&r.pipeline_layout));
    VkShaderModuleCreateInfo smi{VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO};smi.codeSize=shader.size();smi.pCode=words.data();
    VK_OK(vkCreateShaderModule(r.device,&smi,nullptr,&r.shader));
    VkComputePipelineCreateInfo pci{VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO};pci.layout=r.pipeline_layout;
    pci.stage={VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO};pci.stage.stage=VK_SHADER_STAGE_COMPUTE_BIT;pci.stage.module=r.shader;pci.stage.pName="main";
    VK_OK(vkCreateComputePipelines(r.device,VK_NULL_HANDLE,1,&pci,nullptr,&r.pipeline));
    VkCommandPoolCreateInfo cpi{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};cpi.queueFamilyIndex=family;
    VK_OK(vkCreateCommandPool(r.device,&cpi,nullptr,&r.command_pool));
    VkCommandBufferAllocateInfo cai{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};cai.commandPool=r.command_pool;cai.level=VK_COMMAND_BUFFER_LEVEL_PRIMARY;cai.commandBufferCount=1;
    VkCommandBuffer commands;VK_OK(vkAllocateCommandBuffers(r.device,&cai,&commands));
    VkCommandBufferBeginInfo begin{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};begin.flags=VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    VK_OK(vkBeginCommandBuffer(commands,&begin));vkCmdBindPipeline(commands,VK_PIPELINE_BIND_POINT_COMPUTE,r.pipeline);
    vkCmdBindDescriptorSets(commands,VK_PIPELINE_BIND_POINT_COMPUTE,r.pipeline_layout,0,1,&set,0,nullptr);vkCmdDispatch(commands,1,1,1);
    VkMemoryBarrier barrier{VK_STRUCTURE_TYPE_MEMORY_BARRIER};barrier.srcAccessMask=VK_ACCESS_SHADER_WRITE_BIT;barrier.dstAccessMask=VK_ACCESS_HOST_READ_BIT;
    vkCmdPipelineBarrier(commands,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_PIPELINE_STAGE_HOST_BIT,0,1,&barrier,0,nullptr,0,nullptr);
    VK_OK(vkEndCommandBuffer(commands));
    VkSubmitInfo submit{VK_STRUCTURE_TYPE_SUBMIT_INFO};submit.commandBufferCount=1;submit.pCommandBuffers=&commands;
    VK_OK(vkQueueSubmit(queue,1,&submit,VK_NULL_HANDLE));VK_OK(vkQueueWaitIdle(queue));
    if(!coherent)VK_OK(vkInvalidateMappedMemoryRanges(r.device,1,&range));
    std::ofstream output(argv[3],std::ios::binary);output.write(static_cast<const char*>(r.mapped),state.size());
    if(!output)throw std::runtime_error("Cannot write output register state");
    std::cout<<"Executed on "<<properties.deviceName<<"; Vulkan "<<VK_API_VERSION_MAJOR(properties.apiVersion)<<'.'<<VK_API_VERSION_MINOR(properties.apiVersion)<<"; "<<state.size()<<" state bytes\n";
} catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
