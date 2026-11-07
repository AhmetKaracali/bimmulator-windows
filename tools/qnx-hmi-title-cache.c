/* Read-only X20511I HMI title-cache probe. Layouts from the matched ARM ELF. */
typedef unsigned int word;
extern int open(const char *, int, ...);
extern int close(int);
extern int read(int, void *, unsigned int);
extern long long lseek64(int, long long, int);
extern int snprintf(char *, unsigned int, const char *, ...);
extern int printf(const char *, ...);
extern int fflush(void *);
extern void _exit(int);

static int read_at(int fd, word address, void *out, unsigned size)
{
    return address && lseek64(fd, address, 0) == address && read(fd, out, size) == (int)size;
}

static word pointer_at(int fd, word address)
{
    word value;
    return read_at(fd, address, &value, sizeof(value)) ? value : 0;
}

static word linked_base(int fd, word slot, word offset, word prologue)
{
    word entry = pointer_at(fd, slot);
    if (entry <= offset || pointer_at(fd, entry) != prologue)
        return 0;
    word base = entry - offset;
    return pointer_at(fd, base) == 0x464c457f ? base : 0;
}

static word find_plugin_cache(int fd, word plugin)
{
    const char identifier[] = "IHmiResourceManager";
    /* libhmiplugin's identifier-to-cache registry. */
    word buckets = pointer_at(fd, plugin + 0x3061c);
    word count = pointer_at(fd, plugin + 0x30620);
    if (!buckets || !count || count > 1024)
        return 0;
    for (word i = 0; i < count; i++) {
        word node = pointer_at(fd, buckets + 4 * i);
        for (unsigned depth = 0; node && depth < 64; depth++) {
            word entry[3];
            char name[sizeof(identifier)];
            if (!read_at(fd, node, entry, sizeof(entry)))
                break;
            if (entry[0] > 12 && pointer_at(fd, entry[0] - 12) == sizeof(identifier) - 1 &&
                read_at(fd, entry[0], name, sizeof(name))) {
                unsigned j = 0;
                while (j < sizeof(name) && name[j] == identifier[j])
                    j++;
                if (j == sizeof(name))
                    return entry[1];
            }
            node = entry[2];
        }
    }
    return 0;
}

static int print_title(int fd, word root, word handle)
{
    word node = root;
    for (unsigned depth = 0; node && depth < 64; depth++) {
        word entry[7];
        if (!read_at(fd, node, entry, sizeof(entry)))
            goto unreadable;
        /* The tree stores a handle followed by the string and its UTF-16 storage. */
        if (entry[4] != handle) {
            node = entry[handle < entry[4] ? 2 : 3];
            continue;
        }
        word length;
        unsigned short text[96];
        word address = entry[6];
        if (address < 12 || !read_at(fd, address - 12, &length, sizeof(length)) ||
            length > 96 || (length && !read_at(fd, address, text, length * sizeof(text[0]))))
            goto unreadable;
        printf("ID6_TITLE handle=0x%08x units=%u text=", handle, length);
        for (word i = 0; i < length; i++) {
            if (text[i] >= 32 && text[i] <= 126)
                printf("%c", (int)text[i]);
            else
                printf("\\u%04x", (unsigned)text[i]);
        }
        printf("\n");
        return 0;
    }
    printf("ID6_TITLE handle=0x%08x %s\n", handle, node ? "depth-limit" : "absent");
    return 1;

unreadable:
    printf("ID6_TITLE handle=0x%08x unreadable node=0x%08x\n", handle, node);
    return 1;
}

static int inspect_manager(int fd, word manager, word db)
{
    word cache = pointer_at(fd, manager + 0x9c);
    word root = cache ? pointer_at(fd, cache + 0x50) : 0;
    unsigned char language = 0;
    read_at(fd, manager + 0x14, &language, sizeof(language));
    printf("ID6_TITLE_MANAGER object=0x%08x language=%u cache=0x%08x root=0x%08x\n",
           manager, (unsigned)language, cache, root);
    if (!cache || pointer_at(fd, cache) != db + 0x14ddf8 || !root)
        return 1;
    /* Media/Radio, ConnectedDrive, My Vehicle, Notifications. */
    const word titles[] = {0x2000c6d8, 0x20001f90, 0x20010758, 0x20010760};
    int status = 0;
    for (unsigned i = 0; i < sizeof(titles) / sizeof(titles[0]); i++)
        status |= print_title(fd, root, titles[i]);
    return status;
}

static int inspect_hmi(int fd)
{
    if (pointer_at(fd, 0x227790) != 0xe92d4df0 || pointer_at(fd, 0x227794) != 0xe28db01c) {
        printf("ID6_TITLE_ERROR unexpected HmiMain3D image\n");
        return 1;
    }
    /* Resolve both libraries using their imported function slots in HmiMain3D. */
    word plugin = linked_base(fd, 0x38338b0, 0x17db0, 0xe92d4ff0);
    word db = linked_base(fd, 0x3834fc0, 0x84b5c, 0xe92d4ff0);
    printf("ID6_TITLE_LIBS hmiplugin=0x%08x hmidb=0x%08x\n", plugin, db);
    if (!plugin || !db)
        return 1;
    word cache = find_plugin_cache(fd, plugin);
    if (!cache || pointer_at(fd, cache) != plugin + 0x300f8) {
        printf("ID6_TITLE_ERROR plugin cache unavailable address=0x%08x\n", cache);
        return 1;
    }
    /* Each registered thread has a plugin scope with its resource manager. */
    word buckets = pointer_at(fd, cache + 0x18);
    word count = pointer_at(fd, cache + 0x1c);
    if (!buckets || !count || count > 1024)
        return 1;
    for (word i = 0; i < count; i++) {
        word node = pointer_at(fd, buckets + 4 * i);
        for (unsigned depth = 0; node && depth < 64; depth++) {
            word entry[3];
            if (!read_at(fd, node, entry, sizeof(entry)))
                break;
            if (entry[1] && pointer_at(fd, entry[1]) == plugin + 0x30120) {
                word manager = pointer_at(fd, entry[1] + 8);
                if (manager && pointer_at(fd, manager) == db + 0x14dca8)
                    return inspect_manager(fd, manager, db);
                if (manager)
                    printf("ID6_TITLE_MANAGER_CANDIDATE object=0x%08x vptr=0x%08x\n",
                           manager, pointer_at(fd, manager));
            }
            node = entry[2];
        }
    }
    printf("ID6_TITLE_ERROR resource manager unavailable\n");
    return 1;
}

static int run(void)
{
    char input[16], path[40];
    int bytes = read(0, input, sizeof(input));
    word pid = 0;
    int i = 0;
    while (i < bytes && input[i] >= '0' && input[i] <= '9' && pid < 100000000) {
        pid = 10 * pid + (word)(input[i] - '0');
        i++;
    }
    if (!pid || i == bytes || input[i] != '\n')
        return 2;
    snprintf(path, sizeof(path), "/proc/%u/as", pid);
    int fd = open(path, 0);
    if (fd < 0) {
        printf("ID6_TITLE_ERROR cannot open %s\n", path);
        return 1;
    }
    int result = inspect_hmi(fd);
    close(fd);
    return result;
}

void _start(void)
{
    int result = run();
    printf("ID6_TITLE_DONE status=%d\n", result);
    fflush((void *)0);
    _exit(result);
}
