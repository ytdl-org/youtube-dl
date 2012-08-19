#include <stdio.h> 
#include <string.h> 
#include <assert.h> 
#include <stdint.h> 
 
#define FLVF_HEADER 1 
#define FLVF_SCRIPT 2 
 
struct flvhdr 
{ 
    char fh_magic[3]; 
    char fh_version; 
    char fh_flags; 
    char fh_hlen[4]; 
    char fh_pads[4]; 
}__attribute__((packed)); 
 
struct taghdr 
{ 
    uint8_t th_type; 
    uint8_t th_dlen[3]; 
    uint8_t th_tstamp[3]; 
    uint8_t th_xstamp; 
    uint8_t th_streamid[3]; 
}__attribute__((packed)); 
 
struct flvcombine 
{ 
    FILE * fc_file; 
    uint32_t fc_flags; 
    uint32_t fc_timestamp; 
    uint32_t fc_filesize; 
    double fc_duration; 
    int fc_filesize_offset; 
    int fc_duration_offset; 
}; 
 
/* duration, filesize */ 
 
uint32_t buftoint(const void *buf, size_t len) 
{ 
    uint32_t bufint = 0; 
    const uint8_t *pval = (const uint8_t *)buf; 
    while (len-- > 0) 
        bufint = (bufint << 8) + *pval++; 
    return bufint; 
} 
 
int dd_copy(FILE * dst_fp, FILE * src_fp, size_t dlen) 
{ 
    size_t len; 
    char buf[64 * 1024]; 
    while (dlen > 0 && !feof(src_fp)) { 
         len = fread(buf, 1, dlen < sizeof(buf)? dlen: sizeof(buf), src_fp); 
        if (fwrite(buf, 1, len, dst_fp) != len) 
            break; 
        dlen -= len; 
    } 
    return dlen; 
} 
 
void adjtimestamp(struct taghdr *header, uint32_t stampbase) 
{ 
    uint32_t netval = 0; 
    uint32_t adjtime = stampbase; 
    adjtime += buftoint(&header->th_tstamp, sizeof(header->th_tstamp)); 
    adjtime += (header->th_xstamp << 24); 
    header->th_xstamp = (adjtime >> 24); 
    header->th_tstamp[0] = (adjtime >> 16); 
    header->th_tstamp[1] = (adjtime >> 8); 
    header->th_tstamp[2] = (adjtime >> 0); 
} 
 
void update_metainfo(struct flvcombine *combine, FILE *fp, size_t dlen) 
{ 
    int i; 
    size_t len; 
    char *pmem = NULL; 
    char buf[256 * 1024]; 
    double duration = 0.0; 
    uint8_t duration_bytes[8]; 
    printf("dlen: %d\n", dlen); 
    assert (dlen < (256 * 1024)); 
 
    len = fread(buf, 1, dlen < sizeof(buf)? dlen: sizeof(buf), fp); 
    if (len == 0) 
        return; 
    pmem = (char *)memmem(buf, len, "duration", 8); 
    if (pmem == NULL || pmem + 17l - buf > len) 
        return; 
    memcpy(&duration_bytes, pmem + 9, 8); 
    for (i = 0; i < 4; i ++) { 
        uint8_t tmp = duration_bytes[i]; 
        duration_bytes[i] = duration_bytes[7 - i]; 
        duration_bytes[7 - i] = tmp; 
    } 
    memcpy(&duration, &duration_bytes, 8); 
    combine->fc_duration += duration; 
    if (combine->fc_flags & FLVF_SCRIPT) 
        return; 
       combine->fc_duration_offset = 
        combine->fc_filesize + (pmem + 9l - buf) + sizeof(struct taghdr); 
    pmem = (char *)memmem(buf, len, "filesize", 8); 
    if (pmem == NULL || pmem + 17l - buf > len) 
        return; 
    combine->fc_filesize_offset = 
        combine->fc_filesize + (pmem + 9l - buf) + sizeof(struct taghdr); 
} 
 
int addflv(struct flvcombine *combine, const char *path) 
{ 
    int error = 0; 
    FILE *fp, *fout; 
    char magic[4]; 
    long savepos; 
    size_t len, dlen, flags; 
    struct flvhdr header; 
    struct taghdr *last; 
    struct taghdr tagvideo; 
    struct taghdr tagaudio; 
    struct taghdr tagheader; 
 
    fp = fopen(path, "rb"); 
    fout = combine->fc_file; 
    if (fp == NULL || fout == NULL) 
        return 0; 
 
    last = NULL; 
    memset(magic, 0, sizeof(magic)); 
    memset(&tagvideo, 0, sizeof(tagvideo)); 
    memset(&tagaudio, 0, sizeof(tagaudio)); 
 
    if ( !fread(&header, sizeof(header), 1, fp) ) 
        goto fail; 
 
    memcpy(magic, header.fh_magic, 3); 
    if ( strcmp("FLV", magic) ) 
        goto fail; 
 
    if ((combine->fc_flags & FLVF_HEADER) == 0) { 
        fwrite(&header, sizeof(header), 1, fout); 
         combine->fc_filesize += sizeof(header); 
        combine->fc_flags |= FLVF_HEADER; 
    } 
 
    printf("magic: %s\n", magic); 
    printf("flags: 0x%02x\n", header.fh_flags); 
    printf("version: 0x%02x\n", header.fh_version); 
    printf("header len: %d\n", buftoint(header.fh_hlen, sizeof(header.fh_hlen))); 
 
    while (feof(fp) == 0) { 
        if ( !fread(&tagheader, sizeof(tagheader), 1, fp) ) 
            goto fail; 
 
        dlen = buftoint(tagheader.th_dlen, sizeof(tagheader.th_dlen)); 
 
        switch (tagheader.th_type) 
        { 
            case 0x09: 
                adjtimestamp(&tagheader, combine->fc_timestamp); 
                tagvideo = tagheader; 
                last = &tagvideo; 
                break; 
            case 0x08: 
                adjtimestamp(&tagheader, combine->fc_timestamp); 
                tagaudio = tagheader; 
                last = &tagaudio; 
                break; 
            default: 
                flags = combine->fc_flags; 
                savepos = ftell(fp); 
                if (savepos == -1) 
                    goto fail; 
                savepos = (flags & FLVF_SCRIPT)? (savepos + dlen + 4): savepos; 
                update_metainfo(combine, fp, dlen); 
                 combine->fc_flags |= FLVF_SCRIPT; 
                if ( fseek(fp, savepos, SEEK_SET) ) 
                    goto fail; 
                if (flags & FLVF_SCRIPT) 
                    continue; 
                break; 
        } 
         fwrite(&tagheader, sizeof(tagheader), 1, fout); 
         combine->fc_filesize += sizeof(tagheader); 
        combine->fc_filesize += (dlen + 4); 
         if ( dd_copy(fout, fp, dlen + 4)) { 
            error = -__LINE__; 
            break; 
        } 
    } 
 
fail: 
    fclose(fp); 
    if (last == &tagvideo || last == &tagaudio) { 
        combine->fc_timestamp = buftoint(last->th_tstamp, sizeof(last->th_tstamp)); 
        combine->fc_timestamp |= (last->th_xstamp << 24); 
        printf("time stamp: %d\n", combine->fc_timestamp); 
    } 
    return 0; 
} 
 
void fixedflv(struct flvcombine *context) 
{ 
    int i; 
    double dblval = 0.0; 
    uint8_t dblbytes[8]; 
    FILE *fout = context->fc_file; 
 
    if (context->fc_filesize_offset > 0) { 
        if ( fseek(fout, context->fc_filesize_offset, SEEK_SET) ) 
            return; 
        dblval = context->fc_filesize; 
        memcpy(dblbytes, &dblval, 8); 
     
        for (i = 0; i < 4; i ++) { 
             uint8_t tmp = dblbytes[i]; 
             dblbytes[i] = dblbytes[7 - i]; 
             dblbytes[7 - i] = tmp; 
         } 
        fwrite(dblbytes, 8, 1, fout); 
    } 
 
    if (context->fc_duration_offset > 0) { 
        if ( fseek(fout, context->fc_duration_offset, SEEK_SET) ) 
            return; 
        dblval = context->fc_duration; 
        memcpy(dblbytes, &dblval, 8); 
 
        for (i = 0; i < 4; i ++) { 
             uint8_t tmp = dblbytes[i]; 
             dblbytes[i] = dblbytes[7 - i]; 
             dblbytes[7 - i] = tmp; 
         } 
        fwrite(dblbytes, 8, 1, fout); 
    } 
} 
 
int main(int argc, char *argv[]) 
{ 
    int i; 
    struct flvcombine context; 
    memset(&context, 0, sizeof(context)); 
    context.fc_file = fopen("out.flv", "wb"); 
    if (context.fc_file == NULL) 
        return -1; 
    context.fc_duration = 0; 
    for (i = 1; i < argc; i++) 
        addflv(&context, argv[i]); 
    fixedflv(&context); 
    fclose(context.fc_file); 
 
    printf("seconds: %d\n", context.fc_timestamp); 
    return 0; 
} 
