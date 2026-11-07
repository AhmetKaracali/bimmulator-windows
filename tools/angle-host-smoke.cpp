#define EGL_EGLEXT_PROTOTYPES 1
#define GL_GLEXT_PROTOTYPES 1

#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <EGL/eglext_angle.h>
#include <GLES2/gl2.h>

#include <array>
#include <cstddef>
#include <cstdlib>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iterator>
#include <string>

namespace {

constexpr EGLint kSurfaceSize = 64;

int fail(const char *operation, EGLDisplay display = EGL_NO_DISPLAY)
{
    if (display != EGL_NO_DISPLAY) {
        std::fprintf(stderr, "ANGLE_SMOKE_FAIL %s egl=0x%04x\n",
                     operation, eglGetError());
    } else {
        std::fprintf(stderr, "ANGLE_SMOKE_FAIL %s\n", operation);
    }
    return 1;
}

GLuint compile(GLenum type, const char *source)
{
    const GLuint shader = glCreateShader(type);
    if (!shader) {
        return 0;
    }
    glShaderSource(shader, 1, &source, nullptr);
    glCompileShader(shader);
    GLint compiled = GL_FALSE;
    glGetShaderiv(shader, GL_COMPILE_STATUS, &compiled);
    if (compiled != GL_TRUE) {
        char log[1024] = {};
        glGetShaderInfoLog(shader, sizeof(log), nullptr, log);
        std::fprintf(stderr, "ANGLE_SMOKE_SHADER_FAIL type=0x%x %s\n",
                     type, log);
        glDeleteShader(shader);
        return 0;
    }
    return shader;
}

std::string read_source(const char *path)
{
    std::ifstream input(path, std::ios::binary);
    if (!input) {
        std::fprintf(stderr, "ANGLE_SMOKE_SOURCE_FAIL path=%s\n", path);
        return {};
    }
    return {std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
}

} // namespace

int main(int argc, char **argv)
{
    if (argc != 1 && argc != 3) {
        std::fprintf(stderr,
                     "Usage: %s [VERTEX_ESSL FRAGMENT_ESSL]\n", argv[0]);
        return 2;
    }
    const bool file_pair = argc == 3;
    const char *compile_only_value =
        std::getenv("IDRIVE_ANGLE_SMOKE_COMPILE_ONLY");
    const bool compile_only = compile_only_value &&
        std::strcmp(compile_only_value, "1") == 0;
    int context_version = 2;
    if (const char *requested = std::getenv("IDRIVE_ANGLE_GLES_VERSION")) {
        context_version = std::atoi(requested);
        if (context_version != 2 && context_version != 3) {
            std::fprintf(stderr,
                         "ANGLE_SMOKE_VERSION_FAIL expected 2 or 3, got %s\n",
                         requested);
            return 2;
        }
    }
    const std::string vertex_file = file_pair ? read_source(argv[1]) : std::string();
    const std::string fragment_file = file_pair ? read_source(argv[2]) : std::string();
    if (file_pair && (vertex_file.empty() || fragment_file.empty())) return 2;
#if defined(__APPLE__)
    constexpr EGLint kBackend = EGL_PLATFORM_ANGLE_TYPE_METAL_ANGLE;
    constexpr const char *kBackendName = "metal";
#else
    constexpr EGLint kBackend = EGL_PLATFORM_ANGLE_TYPE_VULKAN_ANGLE;
    constexpr const char *kBackendName = "vulkan";
#endif

    const EGLAttrib platform_attributes[] = {
        EGL_PLATFORM_ANGLE_TYPE_ANGLE, kBackend,
        EGL_NONE,
    };
    const EGLDisplay display = eglGetPlatformDisplay(
        EGL_PLATFORM_ANGLE_ANGLE, nullptr, platform_attributes);
    if (display == EGL_NO_DISPLAY) {
        return fail("get-platform-display");
    }

    EGLint major = 0;
    EGLint minor = 0;
    if (eglInitialize(display, &major, &minor) != EGL_TRUE) {
        return fail("initialize", display);
    }
    if (eglBindAPI(EGL_OPENGL_ES_API) != EGL_TRUE) {
        return fail("bind-api", display);
    }

    const EGLint config_attributes[] = {
        EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
        EGL_RENDERABLE_TYPE, context_version == 3
            ? EGL_OPENGL_ES2_BIT | EGL_OPENGL_ES3_BIT_KHR
            : EGL_OPENGL_ES2_BIT,
        EGL_RED_SIZE, 8,
        EGL_GREEN_SIZE, 8,
        EGL_BLUE_SIZE, 8,
        EGL_ALPHA_SIZE, 8,
        EGL_DEPTH_SIZE, 24,
        EGL_NONE,
    };
    EGLConfig config = nullptr;
    EGLint config_count = 0;
    if (eglChooseConfig(display, config_attributes, &config, 1,
                        &config_count) != EGL_TRUE || config_count != 1) {
        return fail("choose-config", display);
    }
    EGLint depth_bits = 0;
    if (eglGetConfigAttrib(display, config, EGL_DEPTH_SIZE, &depth_bits) != EGL_TRUE ||
        depth_bits < 24) {
        return fail("depth24-config", display);
    }

    const EGLint surface_attributes[] = {
        EGL_WIDTH, kSurfaceSize,
        EGL_HEIGHT, kSurfaceSize,
        EGL_NONE,
    };
    const EGLSurface surface =
        eglCreatePbufferSurface(display, config, surface_attributes);
    if (surface == EGL_NO_SURFACE) {
        return fail("create-pbuffer", display);
    }

    const EGLint context_attributes[] = {
        EGL_CONTEXT_CLIENT_VERSION, context_version,
        EGL_NONE,
    };
    const EGLContext context =
        eglCreateContext(display, config, EGL_NO_CONTEXT, context_attributes);
    if (context == EGL_NO_CONTEXT) {
        return fail("create-context", display);
    }
    if (eglMakeCurrent(display, surface, surface, context) != EGL_TRUE) {
        return fail("make-current", display);
    }

    GLint shader_binary_format_count = 0;
    glGetIntegerv(GL_NUM_SHADER_BINARY_FORMATS, &shader_binary_format_count);
    if (glGetError() != GL_NO_ERROR || shader_binary_format_count < 0 ||
        shader_binary_format_count > 16) {
        return fail("shader-binary-format-count", display);
    }
    std::array<GLint, 16> shader_binary_formats = {};
    if (shader_binary_format_count > 0) {
        glGetIntegerv(GL_SHADER_BINARY_FORMATS, shader_binary_formats.data());
        if (glGetError() != GL_NO_ERROR) {
            return fail("shader-binary-formats", display);
        }
    }
    const char *extensions = reinterpret_cast<const char *>(
        glGetString(GL_EXTENSIONS));
    const bool has_spirv_extension = extensions &&
        std::strstr(extensions, "GL_EXT_spirv") != nullptr;
    std::printf("ANGLE_SHADER_BINARY_FORMATS count=%d spirv_extension=%d",
                shader_binary_format_count, has_spirv_extension ? 1 : 0);
    for (GLint i = 0; i < shader_binary_format_count; ++i) {
        std::printf(" 0x%04x", static_cast<unsigned>(shader_binary_formats[i]));
    }
    std::printf("\n");

    constexpr char smoke_vertex_source[] =
        "attribute vec2 a_position;\n"
        "void main() { gl_Position = vec4(a_position, 0.0, 1.0); }\n";
    constexpr char smoke_fragment_source[] =
        "precision mediump float;\n"
        "uniform vec4 u_color;\n"
        "void main() { gl_FragColor = u_color; }\n";
    const GLuint vertex_shader = compile(
        GL_VERTEX_SHADER, file_pair ? vertex_file.c_str() : smoke_vertex_source);
    const GLuint fragment_shader = compile(
        GL_FRAGMENT_SHADER, file_pair ? fragment_file.c_str() : smoke_fragment_source);
    if (!vertex_shader || !fragment_shader) {
        return fail("compile-shader", display);
    }

    const GLuint program = glCreateProgram();
    glAttachShader(program, vertex_shader);
    glAttachShader(program, fragment_shader);
    if (!file_pair) glBindAttribLocation(program, 0, "a_position");
    glLinkProgram(program);
    GLint linked = GL_FALSE;
    glGetProgramiv(program, GL_LINK_STATUS, &linked);
    if (linked != GL_TRUE) {
        char log[1024] = {};
        glGetProgramInfoLog(program, sizeof(log), nullptr, log);
        std::fprintf(stderr, "ANGLE_SMOKE_LINK_FAIL %s\n", log);
        return fail("link-program", display);
    }
    if (compile_only) {
        std::printf("ANGLE_SMOKE_COMPILE_LINK_OK mode=%s backend=%s gles=%d\n",
                    file_pair ? "shader-pair" : "generic",
                    kBackendName, context_version);
        return 0;
    }

    constexpr std::array<GLfloat, 6> smoke_vertices = {
        -1.0f, -1.0f,
         3.0f, -1.0f,
        -1.0f,  3.0f,
    };
    constexpr std::array<GLfloat, 12> rectangle_vertices = {
        -1.0f, -1.0f, 0.0f, 1.0f,
         3.0f, -1.0f, 0.0f, 1.0f,
        -1.0f,  3.0f, 0.0f, 1.0f,
    };
    const GLint attribute = glGetAttribLocation(
        program, file_pair ? "a_Position" : "a_position");
    if (attribute < 0) return fail("attribute-location", display);
    glViewport(0, 0, kSurfaceSize, kSurfaceSize);
    glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);
    glUseProgram(program);
    if (file_pair) {
        constexpr std::array<GLfloat, 16> identity = {
            1.0f, 0.0f, 0.0f, 0.0f,
            0.0f, 1.0f, 0.0f, 0.0f,
            0.0f, 0.0f, 1.0f, 0.0f,
            0.0f, 0.0f, 0.0f, 1.0f,
        };
        const GLint matrix = glGetUniformLocation(program, "u_MVPMatrix");
        const GLint color = glGetUniformLocation(program, "u_color");
        if (matrix < 0 || color < 0) return fail("rectangle-uniform-locations", display);
        glUniformMatrix4fv(matrix, 1, GL_FALSE, identity.data());
        glUniform4f(color, 0.2f, 0.6f, 0.9f, 1.0f);
        glVertexAttribPointer(static_cast<GLuint>(attribute), 4, GL_FLOAT,
                              GL_FALSE, 0, rectangle_vertices.data());
    } else {
        glUniform4f(glGetUniformLocation(program, "u_color"),
                    0.2f, 0.6f, 0.9f, 1.0f);
        glVertexAttribPointer(static_cast<GLuint>(attribute), 2, GL_FLOAT,
                              GL_FALSE, 0, smoke_vertices.data());
    }
    glEnableVertexAttribArray(static_cast<GLuint>(attribute));
    glDrawArrays(GL_TRIANGLES, 0, 3);
    glFinish();
    if (glGetError() != GL_NO_ERROR) {
        return fail("draw", display);
    }
    if (eglSwapBuffers(display, surface) != EGL_TRUE) {
        return fail("swap", display);
    }

    std::array<GLubyte, 4> pixel = {};
    glReadPixels(kSurfaceSize / 2, kSurfaceSize / 2, 1, 1,
                 GL_RGBA, GL_UNSIGNED_BYTE, pixel.data());
    if (glGetError() != GL_NO_ERROR) {
        return fail("read-pixel", display);
    }
    constexpr std::array<int, 4> expected = {51, 153, 230, 255};
    for (std::size_t i = 0; i < pixel.size(); ++i) {
        const int difference = static_cast<int>(pixel[i]) - expected[i];
        if (difference < -4 || difference > 4) {
            std::fprintf(stderr,
                         "ANGLE_SMOKE_PIXEL_FAIL got=%u,%u,%u,%u expected=51,153,230,255\n",
                         pixel[0], pixel[1], pixel[2], pixel[3]);
            return 1;
        }
    }

    const char *renderer = reinterpret_cast<const char *>(glGetString(GL_RENDERER));
    const char *version = reinterpret_cast<const char *>(glGetString(GL_VERSION));
    std::printf("ANGLE_SMOKE_OK mode=%s backend=%s egl=%d.%d gles=%d depth=%d renderer=%s version=%s pixel=%u,%u,%u,%u\n",
                file_pair ? "shader-pair" : "generic",
                kBackendName, major, minor, context_version, depth_bits,
                renderer ? renderer : "(null)",
                version ? version : "(null)",
                pixel[0], pixel[1], pixel[2], pixel[3]);

    glDisableVertexAttribArray(static_cast<GLuint>(attribute));
    glUseProgram(0);
    glDetachShader(program, vertex_shader);
    glDetachShader(program, fragment_shader);
    glDeleteProgram(program);
    glDeleteShader(vertex_shader);
    glDeleteShader(fragment_shader);
    eglMakeCurrent(display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
    eglDestroyContext(display, context);
    eglDestroySurface(display, surface);
    eglTerminate(display);
    return 0;
}
