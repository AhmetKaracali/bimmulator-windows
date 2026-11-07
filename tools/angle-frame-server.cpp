#define EGL_EGLEXT_PROTOTYPES 1
#define GL_GLEXT_PROTOTYPES 1

#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <EGL/eglext_angle.h>
#include <GLES2/gl2.h>

#include "angle-frame-rpc.h"

#include <arpa/inet.h>
#include <cerrno>
#include <chrono>
#include <csignal>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <netinet/in.h>
#include <string>
#include <sys/socket.h>
#include <unistd.h>
#include <vector>

namespace {

bool read_all(int fd, unsigned char *data, std::size_t size,
              std::chrono::steady_clock::time_point *first_byte_time = nullptr)
{
    std::size_t received = 0;
    while (received < size) {
        const ssize_t result = recv(fd, data + received, size - received, 0);
        if (result <= 0) {
            return false;
        }
        if (received == 0 && first_byte_time) {
            *first_byte_time = std::chrono::steady_clock::now();
        }
        received += static_cast<std::size_t>(result);
    }
    return true;
}

bool write_all(int fd, const unsigned char *data, std::size_t size)
{
    std::size_t sent = 0;
    while (sent < size) {
        const ssize_t result = send(fd, data + sent, size - sent, 0);
        if (result <= 0) {
            return false;
        }
        sent += static_cast<std::size_t>(result);
    }
    return true;
}

GLuint compile_shader(GLenum type, const char *source)
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
        std::fprintf(stderr, "ANGLE_RPC_SHADER_FAIL type=0x%x %s\n", type, log);
        glDeleteShader(shader);
        return 0;
    }
    return shader;
}

bool render_frame(unsigned int width, unsigned int height,
                  const unsigned char color[4], std::vector<unsigned char> &pixels)
{
#if defined(__APPLE__)
    constexpr EGLint backend = EGL_PLATFORM_ANGLE_TYPE_METAL_ANGLE;
    constexpr const char *backend_name = "metal";
#else
    constexpr EGLint backend = EGL_PLATFORM_ANGLE_TYPE_VULKAN_ANGLE;
    constexpr const char *backend_name = "vulkan";
#endif
    const EGLAttrib platform_attributes[] = {
        EGL_PLATFORM_ANGLE_TYPE_ANGLE, backend,
        EGL_NONE,
    };
    const EGLDisplay display = eglGetPlatformDisplay(
        EGL_PLATFORM_ANGLE_ANGLE, nullptr, platform_attributes);
    if (display == EGL_NO_DISPLAY) {
        std::fprintf(stderr, "ANGLE_RPC_FAIL stage=get-display egl=0x%04x\n",
                     eglGetError());
        return false;
    }

    EGLint major = 0;
    EGLint minor = 0;
    if (eglInitialize(display, &major, &minor) != EGL_TRUE ||
        eglBindAPI(EGL_OPENGL_ES_API) != EGL_TRUE) {
        std::fprintf(stderr, "ANGLE_RPC_FAIL stage=initialize egl=0x%04x\n",
                     eglGetError());
        eglTerminate(display);
        return false;
    }

    const EGLint config_attributes[] = {
        EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
        EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT,
        EGL_RED_SIZE, 8,
        EGL_GREEN_SIZE, 8,
        EGL_BLUE_SIZE, 8,
        EGL_ALPHA_SIZE, 8,
        EGL_DEPTH_SIZE, 24,
        EGL_NONE,
    };
    EGLConfig config = nullptr;
    EGLint count = 0;
    if (eglChooseConfig(display, config_attributes, &config, 1, &count) != EGL_TRUE ||
        count != 1) {
        std::fprintf(stderr, "ANGLE_RPC_FAIL stage=choose-config egl=0x%04x\n",
                     eglGetError());
        eglTerminate(display);
        return false;
    }
    EGLint depth = 0;
    if (eglGetConfigAttrib(display, config, EGL_DEPTH_SIZE, &depth) != EGL_TRUE ||
        depth < 24) {
        std::fprintf(stderr, "ANGLE_RPC_FAIL stage=depth24 egl=0x%04x depth=%d\n",
                     eglGetError(), depth);
        eglTerminate(display);
        return false;
    }

    const EGLint surface_attributes[] = {
        EGL_WIDTH, static_cast<EGLint>(width),
        EGL_HEIGHT, static_cast<EGLint>(height),
        EGL_NONE,
    };
    const EGLSurface surface =
        eglCreatePbufferSurface(display, config, surface_attributes);
    if (surface == EGL_NO_SURFACE) {
        std::fprintf(stderr, "ANGLE_RPC_FAIL stage=create-pbuffer egl=0x%04x\n",
                     eglGetError());
        eglTerminate(display);
        return false;
    }

    const EGLint context_attributes[] = {
        EGL_CONTEXT_CLIENT_VERSION, 2,
        EGL_NONE,
    };
    const EGLContext context =
        eglCreateContext(display, config, EGL_NO_CONTEXT, context_attributes);
    if (context == EGL_NO_CONTEXT ||
        eglMakeCurrent(display, surface, surface, context) != EGL_TRUE) {
        std::fprintf(stderr, "ANGLE_RPC_FAIL stage=make-current egl=0x%04x\n",
                     eglGetError());
        if (context != EGL_NO_CONTEXT) {
            eglDestroyContext(display, context);
        }
        eglDestroySurface(display, surface);
        eglTerminate(display);
        return false;
    }

    constexpr char vertex_source[] =
        "attribute vec2 a_position;\n"
        "void main() { gl_Position = vec4(a_position, 0.0, 1.0); }\n";
    constexpr char fragment_source[] =
        "precision mediump float;\n"
        "uniform vec4 u_color;\n"
        "void main() { gl_FragColor = u_color; }\n";
    const GLuint vertex = compile_shader(GL_VERTEX_SHADER, vertex_source);
    const GLuint fragment = compile_shader(GL_FRAGMENT_SHADER, fragment_source);
    if (!vertex || !fragment) {
        if (vertex) glDeleteShader(vertex);
        if (fragment) glDeleteShader(fragment);
        eglMakeCurrent(display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
        eglDestroyContext(display, context);
        eglDestroySurface(display, surface);
        eglTerminate(display);
        return false;
    }

    GLuint program = glCreateProgram();
    glAttachShader(program, vertex);
    glAttachShader(program, fragment);
    glBindAttribLocation(program, 0, "a_position");
    glLinkProgram(program);
    GLint linked = GL_FALSE;
    glGetProgramiv(program, GL_LINK_STATUS, &linked);
    if (linked != GL_TRUE) {
        char log[1024] = {};
        glGetProgramInfoLog(program, sizeof(log), nullptr, log);
        std::fprintf(stderr, "ANGLE_RPC_LINK_FAIL %s\n", log);
        linked = GL_FALSE;
    }
    if (linked != GL_TRUE) {
        glDeleteProgram(program);
        glDeleteShader(vertex);
        glDeleteShader(fragment);
        eglMakeCurrent(display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
        eglDestroyContext(display, context);
        eglDestroySurface(display, surface);
        eglTerminate(display);
        return false;
    }

    constexpr GLfloat vertices[] = {
        -1.0f, -1.0f,
         3.0f, -1.0f,
        -1.0f,  3.0f,
    };
    glViewport(0, 0, static_cast<GLsizei>(width), static_cast<GLsizei>(height));
    glDisable(GL_DEPTH_TEST);
    glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    glUseProgram(program);
    glUniform4f(glGetUniformLocation(program, "u_color"),
                color[0] / 255.0f, color[1] / 255.0f,
                color[2] / 255.0f, color[3] / 255.0f);
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, vertices);
    glEnableVertexAttribArray(0);
    glDrawArrays(GL_TRIANGLES, 0, 3);
    glFinish();
    const GLenum draw_error = glGetError();
    const EGLBoolean swapped = eglSwapBuffers(display, surface);
    if (draw_error != GL_NO_ERROR || swapped != EGL_TRUE) {
        std::fprintf(stderr,
                     "ANGLE_RPC_FAIL stage=draw-swap gl=0x%04x egl=0x%04x\n",
                     draw_error, eglGetError());
        glDeleteProgram(program);
        glDeleteShader(vertex);
        glDeleteShader(fragment);
        eglMakeCurrent(display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
        eglDestroyContext(display, context);
        eglDestroySurface(display, surface);
        eglTerminate(display);
        return false;
    }

    pixels.resize(static_cast<std::size_t>(width) * height * 4u);
    glReadPixels(0, 0, static_cast<GLsizei>(width), static_cast<GLsizei>(height),
                 GL_RGBA, GL_UNSIGNED_BYTE, pixels.data());
    const GLenum read_error = glGetError();
    const char *renderer = reinterpret_cast<const char *>(glGetString(GL_RENDERER));
    std::fprintf(stderr,
                 "ANGLE_RPC_RENDER backend=%s egl=%d.%d depth=%d renderer=%s bytes=%zu\n",
                 backend_name, major, minor, depth,
                 renderer ? renderer : "(null)", pixels.size());

    glDisableVertexAttribArray(0);
    glUseProgram(0);
    glDeleteProgram(program);
    glDeleteShader(vertex);
    glDeleteShader(fragment);
    eglMakeCurrent(display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
    eglDestroyContext(display, context);
    eglDestroySurface(display, surface);
    eglTerminate(display);
    return read_error == GL_NO_ERROR;
}

bool serve_client(int client)
{
    std::chrono::steady_clock::time_point service_start;
    unsigned char request[IDRIVE_ANGLE_RPC_REQUEST_SIZE] = {};
    if (!read_all(client, request, sizeof(request), &service_start)) {
        std::fprintf(stderr, "ANGLE_RPC_FAIL stage=read-request\n");
        return false;
    }

    const unsigned int version = idrive_rpc_get_u16(request + 4);
    const unsigned int opcode = idrive_rpc_get_u16(request + 6);
    const unsigned int width = idrive_rpc_get_u32(request + 8);
    const unsigned int height = idrive_rpc_get_u32(request + 12);
    const unsigned int flags = idrive_rpc_get_u32(request + 20);
    const std::size_t payload_size = static_cast<std::size_t>(width) * height * 4u;
    unsigned char response[IDRIVE_ANGLE_RPC_RESPONSE_SIZE] = {};
    std::memcpy(response, "ID6A", 4);
    idrive_rpc_put_u16(response + 4, 1);
    idrive_rpc_put_u32(response + 8, width);
    idrive_rpc_put_u32(response + 12, height);

    if (std::memcmp(request, "ID6R", 4) != 0 || version != 1 || opcode != 1 ||
        width == 0 || height == 0 || width > IDRIVE_ANGLE_RPC_MAX_WIDTH ||
        height > IDRIVE_ANGLE_RPC_MAX_HEIGHT ||
        payload_size > IDRIVE_ANGLE_RPC_MAX_BYTES || flags != 0) {
        idrive_rpc_put_u16(response + 6, 1);
        std::fprintf(stderr,
                     "ANGLE_RPC_REJECT version=%u opcode=%u width=%u height=%u flags=%u\n",
                     version, opcode, width, height, flags);
        (void)write_all(client, response, sizeof(response));
        return false;
    }

    std::vector<unsigned char> pixels;
    const bool rendered = render_frame(width, height, request + 16, pixels);
    if (!rendered || pixels.size() != payload_size) {
        idrive_rpc_put_u16(response + 6, 2);
        std::fprintf(stderr, "ANGLE_RPC_FAIL stage=render\n");
        return write_all(client, response, sizeof(response));
    }

    idrive_rpc_put_u16(response + 6, 0);
    idrive_rpc_put_u32(response + 16, static_cast<unsigned int>(pixels.size()));
    if (!write_all(client, response, sizeof(response)) ||
        !write_all(client, pixels.data(), pixels.size())) {
        std::fprintf(stderr, "ANGLE_RPC_FAIL stage=write-response errno=%d\n", errno);
        return false;
    }
    const auto service_us = std::chrono::duration_cast<std::chrono::microseconds>(
        std::chrono::steady_clock::now() - service_start).count();
    std::fprintf(stderr,
                 "ANGLE_RPC_OK width=%u height=%u payload_bytes=%zu wire_bytes=%zu service_us=%lld\n",
                 width, height, pixels.size(),
                 sizeof(request) + sizeof(response) + pixels.size(),
                 static_cast<long long>(service_us));
    return true;
}

} // namespace

int main(int argc, char **argv)
{
    unsigned int port = IDRIVE_ANGLE_RPC_PORT;
    bool once = false;
    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], "--once") == 0) {
            once = true;
        } else if (std::strcmp(argv[i], "--port") == 0 && i + 1 < argc) {
            char *end = nullptr;
            const unsigned long value = std::strtoul(argv[++i], &end, 10);
            if (!end || *end || value < 1024 || value > 65535) {
                std::fprintf(stderr, "Usage: %s [--port 1024..65535] [--once]\n", argv[0]);
                return 2;
            }
            port = static_cast<unsigned int>(value);
        } else {
            std::fprintf(stderr, "Usage: %s [--port 1024..65535] [--once]\n", argv[0]);
            return 2;
        }
    }

    std::signal(SIGPIPE, SIG_IGN);
    const int listener = socket(AF_INET, SOCK_STREAM, 0);
    if (listener < 0) {
        std::perror("socket");
        return 1;
    }
    const int reuse = 1;
    (void)setsockopt(listener, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));
    sockaddr_in address = {};
#if defined(__APPLE__)
    address.sin_len = sizeof(address);
#endif
    address.sin_family = AF_INET;
    address.sin_port = htons(static_cast<unsigned short>(port));
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (bind(listener, reinterpret_cast<sockaddr *>(&address), sizeof(address)) != 0 ||
        listen(listener, 4) != 0) {
        std::perror("bind/listen");
        close(listener);
        return 1;
    }
    std::fprintf(stderr,
                 "ANGLE_RPC_LISTEN address=127.0.0.1 port=%u once=%u\n",
                 port, once ? 1u : 0u);

    for (;;) {
        sockaddr_in peer = {};
        socklen_t peer_size = sizeof(peer);
        const int client = accept(listener, reinterpret_cast<sockaddr *>(&peer), &peer_size);
        if (client < 0) {
            if (errno == EINTR) {
                continue;
            }
            std::perror("accept");
            close(listener);
            return 1;
        }
        char peer_text[INET_ADDRSTRLEN] = {};
        (void)inet_ntop(AF_INET, &peer.sin_addr, peer_text, sizeof(peer_text));
        std::fprintf(stderr, "ANGLE_RPC_ACCEPT peer=%s port=%u\n",
                     peer_text, ntohs(peer.sin_port));
        const bool completed = serve_client(client);
        close(client);
        if (once && completed) {
            break;
        }
    }
    close(listener);
    return 0;
}
