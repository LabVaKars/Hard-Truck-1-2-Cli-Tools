import os
import struct
import math
import sys
import logging
import copy
from io import BytesIO

import common as c

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger("extract_res")
log.setLevel(logging.DEBUG)

def dec_byte(data, size=1, littleEndian=True):
    order = str('<' if littleEndian else '>')
    format_ = str((None, 'B', 'H', None, 'I')[size])

    return struct.unpack(order + format_, data)[0]


def multiple_dec_byte(stream, num, size=1, littleEndian=True):
    return [dec_byte(stream.read(size), size, littleEndian) for number in range(num)]


def gen_byte(data, size=1, littleEndian=True):
    order = str('<' if littleEndian else '>')
    format_ = str((None, 'B', 'H', None, 'I')[size])
    if size == 3:
        return struct.pack(order + 'BBB', data)
    return struct.pack(order + format_, data)

class TGAHeader(object):

    """Header object for TGA files."""

    def __init__(self):
        """Initialize all fields.

        Here we have some details for each field:

        #- Field(1)
        # ID LENGTH (1 byte):
        #   Number of bites of field 6, max 255.
        #   Is 0 if no image id is present.
        #
        #- Field(2)
        # COLOR MAP TYPE (1 byte):
        #   - 0 : no color map included with the image
        #   - 1 : color map included with the image
        #
        #- Field(3)
        # IMAGE TYPE (1 byte):
        #   - 0  : no data included
        #   - 1  : uncompressed color map image
        #   - 2  : uncompressed true color image
        #   - 3  : uncompressed black and white image
        #   - 9  : run-length encoded color map image
        #   - 10 : run-length encoded true color image
        #   - 11 : run-length encoded black and white image
        #
        #- Field(4)
        # COLOR MAP SPECIFICATION (5 bytes):
        #   - first_entry_index (2 bytes) : index of first color map entry
        #   - color_map_length  (2 bytes)
        #   - color_map_entry_size (1 byte)
        #
        #- Field(5)
        # IMAGE SPECIFICATION (10 bytes):
        #   - x_origin  (2 bytes)
        #   - y_origin  (2 bytes)
        #   - image_width   (2 bytes)
        #   - image_height  (2 bytes)
        #   - pixel_depht   (1 byte):
        #       - 8 bit  : grayscale
        #       - 16 bit : RGB (5-5-5-1) bit per color
        #                  Last one is alpha (visible or not)
        #       - 24 bit : RGB (8-8-8) bit per color
        #       - 32 bit : RGBA (8-8-8-8) bit per color
        #   - image_descriptor (1 byte):
        #       - bit 3-0 : number of attribute bit per pixel
        #       - bit 5-4 : order in which pixel data is transferred
        #                   from the file to the screen
        #  +-----------------------------------+-------------+-------------+
        #  | Screen destination of first pixel | Image bit 5 | Image bit 4 |
        #  +-----------------------------------+-------------+-------------+
        #  | bottom left                       |           0 |           0 |
        #  | bottom right                      |           0 |           1 |
        #  | top left                          |           1 |           0 |
        #  | top right                         |           1 |           1 |
        #  +-----------------------------------+-------------+-------------+
        #       - bit 7-6 : must be zero to insure future compatibility
        #
        """
        # Field(1)
        self.id_length = 0
        # Field(2)
        self.color_map_type = 0
        # Field(3)
        self.image_type = 0
        # Field(4)
        self.first_entry_index = 0
        self.color_map_length = 0
        self.color_map_entry_size = 0
        # Field(5)
        self.x_origin = 0
        self.y_origin = 0
        self.image_width = 0
        self.image_height = 0
        self.pixel_depht = 0
        self.image_descriptor = 0

    def from_stream(self, stream):
        self.id_length = dec_byte(stream.read(1))
        self.color_map_type = dec_byte(stream.read(1))
        self.image_type = dec_byte(stream.read(1))
        self.first_entry_index = dec_byte(stream.read(2), 2)
        self.color_map_length = dec_byte(stream.read(2), 2)
        self.color_map_entry_size = dec_byte(stream.read(1))
        self.x_origin = dec_byte(stream.read(2), 2)
        self.y_origin = dec_byte(stream.read(2), 2)
        self.image_width = dec_byte(stream.read(2), 2)
        self.image_height = dec_byte(stream.read(2), 2)
        self.pixel_depht = dec_byte(stream.read(1))
        self.image_descriptor = dec_byte(stream.read(1))

    def to_bytes(self):
        """Convert the object to bytes.

        Returns:
            bytes: the conversion in bytes"""
        tmp = bytearray()

        tmp += gen_byte(self.id_length)
        tmp += gen_byte(self.color_map_type)
        tmp += gen_byte(self.image_type)
        tmp += gen_byte(self.first_entry_index, 2)
        tmp += gen_byte(self.color_map_length, 2)
        tmp += gen_byte(self.color_map_entry_size)
        tmp += gen_byte(self.x_origin, 2)
        tmp += gen_byte(self.y_origin, 2)
        tmp += gen_byte(self.image_width, 2)
        tmp += gen_byte(self.image_height, 2)
        tmp += gen_byte(self.pixel_depht)
        tmp += gen_byte(self.image_descriptor)

        return tmp


class Image:
    def __init__(self, pixels, width, height, order='RGBA', bit_depth='8888'):
        self.width = width
        self.height = height
        self.order = order.upper()
        self.bit_depth = bit_depth
        self._input_depths = Image._parse_bit_depth(bit_depth, order)
        # Store pixels in 8-bit RGBA internally
        self._rgba_pixels = [
            [self._to_rgba8(px, self.order, self._input_depths) for px in row]
            for row in pixels
        ]

    @staticmethod
    def decode_bytearray_to_pixels(data, width, height, bit_depth, channel_order='RGBA'):

        bit_depths = Image._parse_bit_depth(bit_depth, channel_order)
        # dict(zip('RGBA', map(int, bit_depth)))
        channel_order = channel_order.upper()
        # channels = [ch for ch in channel_order if bit_depths[ch] > 0]
        bits_per_pixel = sum(bit_depths[ch] for ch in 'RGBA')
        bytes_per_pixel = (bits_per_pixel + 7) // 8  # Round up

        if len(data) < width * height * bytes_per_pixel:
            raise ValueError("Bytearray is too small for the image size and format.")

        pixels = []
        idx = 0

        for _ in range(height):
            row = []
            for _ in range(width):
                chunk = data[idx:idx + bytes_per_pixel]
                value = int.from_bytes(chunk, byteorder='little')
                idx += bytes_per_pixel

                pixel = {}
                shift = bits_per_pixel
                for ch in channel_order:
                    bits = bit_depths[ch]
                    if bits == 0:
                        continue
                    shift -= bits
                    mask = (1 << bits) - 1
                    pixel[ch] = (value >> shift) & mask

                row.append(tuple(pixel.get(ch, 255 if ch == 'A' else 0) for ch in channel_order))
            pixels.append(row)

        return pixels

    @staticmethod
    def _parse_bit_depth(bit_depth, order='RGBA'):
        if len(bit_depth) == 4:
            return dict(zip(order, map(int, bit_depth)))
        raise ValueError("Unsupported bit depth format")

    @staticmethod
    def _convert_channel_depth(value, from_bits, to_bits):
        if from_bits == to_bits:
            return value
        if (from_bits == 0 or to_bits == 0):
            return 0
        max_from = (1 << from_bits) - 1
        max_to = (1 << to_bits) - 1
        return (value * max_to + (max_from // 2)) // max_from

    def _to_rgba8(self, px, order, input_depths):
        """Convert a pixel from input order/bit-depth to 8-bit RGBA"""
        mapping = dict(zip(order, px))
        rgba = []
        for ch in 'RGBA':
            val = mapping.get(ch, 255 if ch == 'A' else 0)
            bits = input_depths.get(ch, 8)
            if ch == 'A' and bits == 0:
                rgba.append(val)
            else:
                rgba.append(Image._convert_channel_depth(val, bits, 8))
        return tuple(rgba)

    def _from_rgba8(self, rgba, order, output_depths):
        """Convert from 8-bit RGBA to target bit-depth and order"""
        converted = []
        for ch in order:
            val = rgba['RGBA'.index(ch)]
            bits = output_depths.get(ch, 8)
            if ch == 'A' and bits == 0:
                converted.append(val)
            else:
                converted.append(Image._convert_channel_depth(val, 8, bits))
        return tuple(converted)

    def save_as(self, new_bit_depth, channel_order='RGBA'):
        """Convert entire image to a new bit depth and channel order"""
        bit_depths = Image._parse_bit_depth(new_bit_depth, channel_order)
        pixels = [
            [self._from_rgba8(px, channel_order, bit_depths) for px in row]
            for row in self._rgba_pixels
        ]

        bits_per_pixel = sum(bit_depths[ch] for ch in channel_order)
        # bytes_per_pixel = (bits_per_pixel + 7) // 8  # Round up

        # packed_data = bytearray()
        
        out_pixels = []
        for row in pixels:
            for px in row:
                out_row = []
                # Build integer by packing each channel
                shift = bits_per_pixel
                value = 0
                for i, ch in enumerate(channel_order):
                    bits = bit_depths[ch]
                    if bits == 0:
                        continue

                    shift -= bits
                    mask = (1 << bits) - 1
                    value |= (px[i] & mask) << shift

                out_row.append(value)
            out_pixels.append(out_row)

        return out_pixels

    def save_bytes(self, new_bit_depth, channel_order='RGBA'):
        """Convert entire image to a new bit depth and channel order"""
        bit_depths = Image._parse_bit_depth(new_bit_depth, channel_order)
        pixels = [
            [self._from_rgba8(px, channel_order, bit_depths) for px in row]
            for row in self._rgba_pixels
        ]

        bits_per_pixel = sum(bit_depths[ch] for ch in channel_order)
        bytes_per_pixel = (bits_per_pixel + 7) // 8  # Round up
        fmt = {1: 'B', 2: 'H', 4: 'I'}[bytes_per_pixel]

        packed_data = bytearray()
        
        # out_pixels = []
        for row in pixels:
            for px in row:
                # out_row = []
                # Build integer by packing each channel
                shift = bits_per_pixel
                value = 0
                for i, ch in enumerate(channel_order):
                    bits = bit_depths[ch]
                    if bits == 0:
                        continue

                    shift -= bits
                    mask = (1 << bits) - 1
                    value |= (px[i] & mask) << shift

                # Pack into bytes
                packed = struct.pack(('<') + fmt, value)
                packed_data.extend(packed)  
            #     out_row.append(value)
            # out_pixels.append(out_row)

        # return out_pixels
        return bytes(packed_data)

    def get_pixel(self, x, y):
        """Return original pixel format at x, y"""
        rgba = self._rgba_pixels[y][x]
        output_depths = Image._parse_bit_depth(self.bit_depth)
        return self._from_rgba8(rgba, 'RGBA', output_depths)

    def to_array(self):
        """Return full image as 2D array in current format"""
        output_depths = Image._parse_bit_depth(self.bit_depth)
        return [
            [self._from_rgba8(px, self.order, output_depths) for px in row]
            for row in self._rgba_pixels
        ]
    
    def __repr__(self):
        return f"<Image {self.width}x{self.height} in {self.bit_depth} ({self.order})>"



def parse_plm(stream):

    magic = stream.read(4).decode("UTF-8")
    plm_size = struct.unpack("<I", stream.read(4))[0]
    size_left = plm_size
    plm_sections = {
        "PALT" : [],
        "OPAC": [],
        "FOG": [],
        "INTE": [],
        "OP16": [],
        "FO16": [],
        "IN16": []
    } 

    while(size_left > 0):
        sect = stream.read(4).decode("utf-8")
        sect_size = struct.unpack("<I", stream.read(4))[0]

        if sect == "PALT":
            colors = []
            for i in range(sect_size // 3):
                r = struct.unpack("<B",stream.read(1))[0]
                g = struct.unpack("<B",stream.read(1))[0]
                b = struct.unpack("<B",stream.read(1))[0]
                colors.append({
                    "r": r,
                    "g": g,
                    "b": b
                })
            plm_sections["PALT"] = colors

        elif sect == "OPAC":
            blend_cnt = struct.unpack("<I", stream.read(4))[0]  # 9
            opac_depth = struct.unpack("<I", stream.read(4))[0] # 23
            entry_size = struct.unpack("<I", stream.read(4))[0]
            pal_rows = []
            for j in range(blend_cnt):
                pal_indexes = []
                for i in range(opac_depth):
                    indexes = list(struct.unpack("<256B", stream.read(256)))
                    pal_indexes.append(indexes)
                pal_rows.append(pal_indexes)
            plm_sections["OPAC"] = pal_rows
        
        elif sect == "FOG\x00":
            pal_index = struct.unpack("<I", stream.read(4))[0]
            blend_cnt = struct.unpack("<I", stream.read(4))[0]
            entry_size = struct.unpack("<I", stream.read(4))[0]
            blend_indexes = []
            for i in range(blend_cnt):
                indexes = list(struct.unpack("<256B", stream.read(256)))
                blend_indexes.append(indexes)
            plm_sections["FOG"] = blend_indexes
        
        elif sect == "INTE":
            unknown = struct.unpack("<I", stream.read(4))[0]
            blend_cnt = struct.unpack("<I", stream.read(4))[0]
            entry_size = struct.unpack("<I", stream.read(4))[0]
            blend_indexes = []
            for i in range(blend_cnt):
                indexes = list(struct.unpack("<256B", stream.read(256)))
                blend_indexes.append(indexes)
            plm_sections["INTE"] = blend_indexes
        
        elif sect == "OP16": #1555
            blend_cnt = struct.unpack("<I", stream.read(4))[0]  # 1
            opac_depth = struct.unpack("<I", stream.read(4))[0] # 1
            entry_size = struct.unpack("<I", stream.read(4))[0]
            pal_rows = []
            for j in range(blend_cnt):
                pal_indexes = []
                for i in range(opac_depth):
                    color_bytes = list(struct.unpack("<32768H", stream.read(65536)))
                    colors = [{
                        "r": (c>>7)&0xF8, 
                        "g": (c>>2)&0xF8, 
                        "b": (c&0x1F)<<3, 
                    } for c in color_bytes]
                    pal_indexes.append(colors)
                pal_rows.append(pal_indexes)
            plm_sections["OP16"] = pal_rows
        
        elif sect == "FO16": #1555
            pal_index = struct.unpack("<I", stream.read(4))[0] # 1
            blend_cnt = struct.unpack("<I", stream.read(4))[0] # 1
            entry_size = struct.unpack("<I", stream.read(4))[0]
            
            pal_colors = []
            for i in range(blend_cnt):
                color_bytes = list(struct.unpack("<32768H", stream.read(65536)))

                colors = [{
                    "r": (c>>7)&0xF8, 
                    "g": (c>>2)&0xF8, 
                    "b": (c&0x1F)<<3, 
                } for c in color_bytes]
                pal_colors.append(colors)

            plm_sections["FO16"] = pal_colors
        
        elif sect == "IN16": #1555
            unknown = struct.unpack("<I", stream.read(4))[0] # 1
            blend_cnt = struct.unpack("<I", stream.read(4))[0] # 1
            entry_size = struct.unpack("<I", stream.read(4))[0]
            
            pal_colors = []
            for i in range(blend_cnt):
                color_bytes = list(struct.unpack("<32768H", stream.read(65536)))

                colors = [{
                    "r": (c>>7)&0xF8, 
                    "g": (c>>2)&0xF8, 
                    "b": (c&0x1F)<<3, 
                } for c in color_bytes]
                pal_colors.append(colors)

            plm_sections["IN16"] = pal_colors
        
        else: #skip
            stream.read(sect_size)

        size_left -= (sect_size + 8)

    return plm_sections


def palette_to_colors(palette, indexes, trc):
    colors = []
    for index in indexes:
        r = palette[index][0]
        g = palette[index][1]
        b = palette[index][2]
        if (0 | (r << 16) | (g << 8) | b) != (0 | (trc[0] << 16) | (trc[1] << 8) | trc[2]):
            a = 255
        else:
            a = 0
        # colors.extend([r, g, b, a])
        colors.extend([b, g, r, a])
    return colors

def compress_rle(pixels, bytes_per_pixel):
    result = bytearray()
    for row in pixels:
        for repetition_count, pixel_value in compress_row(row):
            result += gen_byte(repetition_count)
            if repetition_count > 127:
                result += gen_byte(pixel_value, bytes_per_pixel)

            else:
                for pixel in pixel_value:
                    result += gen_byte(pixel, bytes_per_pixel)
    
    return result


def compress_row(row):
    repetition_count = None
    pixel_value = None
    ##
    # States:
    # - 0: init
    # - 1: run-length packet
    # - 2: raw packet
    #
    state = 0
    index = 0

    while index != len(row):
        if state == 0:
            repetition_count = 0
            if index == len(row) - 1:
                pixel_value = [row[index]]
                yield (repetition_count, pixel_value)
            elif row[index] == row[index + 1]:
                repetition_count |= 0b10000000
                pixel_value = row[index]
                state = 1
            else:
                pixel_value = [row[index]]
                state = 2
            index += 1
        elif state == 1 and row[index] == pixel_value:
            if repetition_count & 0b1111111 == 127:
                yield (repetition_count, pixel_value)
                repetition_count = 0b10000000
            else:
                repetition_count += 1
            index += 1
        elif state == 2 and row[index] != pixel_value:
            if repetition_count & 0b1111111 == 127:
                yield (repetition_count, pixel_value)
                repetition_count = 0
                pixel_value = [row[index]]
            else:
                repetition_count += 1
                pixel_value.append(row[index])
            index += 1
        else:
            yield (repetition_count, pixel_value)
            state = 0

    if state != 0:
        yield (repetition_count, pixel_value)


def decompress_rle(stream, width, height, bytes_per_pixel):
    try:
        rleBytes = bytearray()
        pixel_count = 0
        decompressed_data = bytearray(width * height * bytes_per_pixel)
        while pixel_count < width * height:
            raw_bit = stream.read(1)
            rleBytes += raw_bit
            curbit = struct.unpack("<B", raw_bit)[0]
            if(curbit > 127): #black pixels
                pixel_count += (curbit-128)
            else: #raw data
                decompressed_data[pixel_count * bytes_per_pixel:(pixel_count + curbit) * bytes_per_pixel] = stream.read(curbit*bytes_per_pixel)
                pixel_count += curbit
        
        return {
            "data": decompressed_data,
            "rle_bytes": rleBytes
        }
    except:
        log.error(stream.tell())
        raise


def read_lvmp(file, bytes_per_pixel):
    mipmaps = []
    mipmap_count = struct.unpack("<i", file.read(4))[0]
    width = struct.unpack("<i", file.read(4))[0] #width
    height = struct.unpack("<i", file.read(4))[0] #height
    mipmap_size = width * height
    l_bytes_per_pixel = struct.unpack("<i", file.read(4))[0] # in HT2 is 2
    for i in range(mipmap_count):
        mipmap = {}
        mipmap['width'] = width
        mipmap['height'] = height
        mipmap['colors'] = file.read(mipmap_size*bytes_per_pixel)
        width = width >> 1
        height = height >> 1
        mipmap_size = width * height
        mipmaps.append(mipmap)

    # TODO: allign instead of hardcoded
    file.read(2) # 2 extra bytes
    return mipmaps


def txr_to_tga32(stream, image_type, tgaDebug):
    
    og_header = TGAHeader()
    og_header.from_stream(stream)
    if og_header.id_length == 12: #LOFF section
        section_identifier = stream.read(4) # LOFF
        section_size = struct.unpack("<i", stream.read(4))[0]
        footer_size = struct.unpack("<i", stream.read(4))[0]

    width = og_header.image_width
    height = og_header.image_height

    # reading original image
    colors_size = height*width
    if image_type == 2:
        colors_before = stream.read(colors_size*2)
    else: # image_type = 1:
        palette_size = og_header.color_map_length*3
        palette_bytes = stream.read(palette_size)
        palette = struct.unpack("<"+str(palette_size)+"B", palette_bytes)
        palette = [palette[i:i+3] for i in range(0, len(palette), 3)]
        colors_size = height*width
        colors_before = stream.read(colors_size)

    header = TGAHeader()

    header.id_length = 0 #IdLength
    header.image_type = 2 
    # header.color_map_length = 32 #ColorMapEntrySize
    header.pixel_depht = 32 #PixelDepth
    header.image_width = width
    header.image_height = height
    header.image_descriptor = 32 #ImageDescriptor

    if image_type == 2: # reading additional sections

        footer_identifier = stream.read(4)
        footer_size = struct.unpack("<i", stream.read(4))[0]
        mipmaps = []
        if footer_identifier == b"LVMP": #skip mipmap section
            mipmaps = read_lvmp(stream, 2)
            footer_identifier = stream.read(4)
            footer_size = struct.unpack("<i", stream.read(4))[0]

        pfrm = list(struct.unpack("<4i", stream.read(16)))  # default pfrm channel order in RGBA
        pfrm = [pfrm[3]] + pfrm[0:3]                        # change it to ARGB to match HT2

        stream.read(footer_size-16)
        bit_depth = ''.join(str(bin(x).count('1')) for x in pfrm)

        mipmap_header = copy.copy(header)
        mipmap_header.id_length = 0
        mipmaps_data = []
        for mipmap in mipmaps:
            mipmapBuffer = BytesIO()
            mipmap_header.image_width = mipmap['width']
            mipmap_header.image_height = mipmap['height']
            mipmapObj = {
                "data": None,
                "h": None,
                "w": None
            }
            mipmap_pixels = Image.decode_bytearray_to_pixels(
                bytearray(mipmap['colors']), 
                mipmap['width'],
                mipmap['height'],
                bit_depth, 'ARGB'
            )
            img = Image(mipmap_pixels, mipmap['width'], mipmap['height'], 'ARGB', bit_depth)
            new_image_bytes = img.save_bytes('8888', 'ARGB')
            mipmapBuffer.write(mipmap_header.to_bytes())
            mipmapBuffer.write(new_image_bytes)
            mipmapObj["data"] = mipmapBuffer
            mipmapObj["h"] = mipmap['height']
            mipmapObj["w"] = mipmap['width']
            mipmaps_data.append(mipmapObj)

    outBuffer = BytesIO()

    # Preparing tga32 image data
    if image_type == 2:

        pixels = Image.decode_bytearray_to_pixels(
            bytearray(colors_before), 
            header.image_width,
            header.image_height,
            bit_depth, 'ARGB'
        )

        img = Image(pixels, header.image_width, header.image_height, 'ARGB', bit_depth)
        img_data = img.save_bytes('8888', 'ARGB')
    
        outBuffer.write(header.to_bytes())
        outBuffer.write(img_data)
    
    else: # image_type == 1:

        colors = list(struct.unpack("<"+str(colors_size)+"B", colors_before))

        transp_color = (0, 0, 0)

        colors_after = palette_to_colors(palette, colors, transp_color)
        outBuffer = BytesIO()

        colors_pack = struct.pack("<"+str(colors_size*4)+"B", *colors_after)
        
        outBuffer.write(header.to_bytes())
        outBuffer.write(colors_pack)

    # saving debug tga
    if tgaDebug:
        debugBuffer = BytesIO()
        debug_header = TGAHeader()
        if image_type == 2:
            debug_header.image_type = 2
            debug_header.color_map_entry_size = 16
            debug_header.pixel_depht = 16
            debug_header.image_width = header.image_width
            debug_header.image_height = header.image_height
            debug_header.image_descriptor = 32

            debugBuffer.write(debug_header.to_bytes())
            debugBuffer.write(colors_before)
        else: # image_type == 1:
            debug_header.image_type = 1
            debug_header.color_map_type = 1
            debug_header.color_map_length = 256
            debug_header.color_map_entry_size = 24
            debug_header.pixel_depht = 8
            debug_header.image_width = header.image_width
            debug_header.image_height = header.image_height
            debug_header.image_descriptor = 32

            debugBuffer.write(debug_header.to_bytes())
            debugBuffer.write(palette_bytes)
            debugBuffer.write(colors_before)

    img_type = 'TIMG' if image_type == 2 else 'CMAP' 

    result = {}
    result['img_type'] = img_type
    result['format'] = pfrm if image_type == 2 else None
    result['mipmaps'] = mipmaps_data if image_type == 2 else []
    result['has_mipmap'] = True if len(result['mipmaps']) > 0 else False
    result['data'] = outBuffer
    result['debug_data'] = debugBuffer if tgaDebug else None

    return result


def generate_palette(colors, width, height, size = 256):
    pixel_indexes = {}

    # Loop through the image data, counting the occurrence of each pixel value
    indexes = [[0 for y in range(len(colors[0]))] for x in range(len(colors))]

    for x, row in enumerate(colors):
        for y, px in enumerate(row):
            pixel_value = px[1] << 16 | px[2] << 8 | px[3]
            if pixel_value not in pixel_indexes:
                pixel_indexes[pixel_value] = []
            pixel_indexes[pixel_value].append((x,y))

    if len(pixel_indexes.keys()) > size:
        log.error("Image doesn't fit {} color palette.".format(size))
        return None

    arr_ind = 0
    palette = [(0, 0, 0) for _ in range(size)]  # Initialize palette with black
    for value, ind in pixel_indexes.items():
        palette[arr_ind] = ((value >> 16) & 255, (value >> 8) & 255, value & 255)
        for x, y in ind:
            indexes[x][y] = arr_ind
        arr_ind += 1

    # Return the palette
    return {
        'palette': palette, 
        'indexes': indexes
    }


def generate_mipmaps(barray, width, height):
    # Load the original image into a 2D array of pixels
    original_image = [[0 for y in range(height)] for x in range(width)]

    for x in range(width):
        for y in range(height):
            color = struct.unpack('>I', barray[(x*width + y) * 4: (x*width + y + 1) * 4])[0]
            original_image[x][y] = (\
                (color >> 8) & 255, \
                (color >> 16) & 255, \
                (color >> 24) & 255, \
                (color >> 0) & 255\
            )

    # Create a list of mip-map levels, starting with the original image
    mipmapObj = {
        "data": original_image,
        "h": height,
        "w": width
    }

    mipmaps = [mipmapObj]

    # Generate the mip-map levels
    while width > 1 or height > 1:
        # Halve the dimensions of the image
        width = math.ceil(width / 2)
        height = math.ceil(height / 2)

        # Create a new 2D array for the mip-map level
        mip_level = [[0 for y in range(height)] for x in range(width)]

        # Compute the average color of each 2x2 block in the previous mip-map level
        for x in range(width):
            for y in range(height):
                r, g, b, a = 0, 0, 0, 0
                count = 0
                for dx in range(2):
                    for dy in range(2):
                        px = 2 * x + dx
                        py = 2 * y + dy
                        if px < len(mipmaps[-1]['data']) and py < len(mipmaps[-1]['data'][0]):
                            pr, pg, pb, pa = mipmaps[-1]['data'][px][py]
                            r += pr
                            g += pg
                            b += pb
                            a += pa
                            count += 1
                if count > 0:
                    r /= count
                    g /= count
                    b /= count
                    a /= count
                mip_level[x][y] = (int(r), int(g), int(b), int(a))

        mipmapObj = {
            "data": mip_level,
            "h": height,
            "w": width
        }
        mipmaps.append(mipmapObj)

    return mipmaps


def convert_txr_to_tga32(stream, tgaDebug):
    image_type = ""
    stream.seek(2, 0)
    image_type = struct.unpack("<B", stream.read(1))[0]
    stream.seek(0, 0)
    log.debug("Image type: {}".format(image_type))
    if image_type in [1, 2]: 
        return txr_to_tga32(stream, image_type, tgaDebug)
    else:
        log.error("Unsupported Tga image type: {}".format(image_type))
    return None


def convert_tga32_to_txr(stream, tex_params, tgaDebug):

    image_type = tex_params['img_type']

    if image_type == 'TIMG':
        return truecolor_tga_32_to_txr(stream, tex_params, tgaDebug)
        pass
    elif image_type == 'CMAP':
        # return colormap_tga_32_to_txr(stream, tex_params, tgaDebug)
        pass

def get_argb_bit_mask(image_format):
    offset = 0
    bit_masks = []
    for i in range(3, -1, -1):
        cur_int = int(image_format[i])
        if cur_int == 0:
            format_int = 0
        else:
            format_int = 1
            for j in range(cur_int-1):
                format_int = format_int << 1
                format_int += 1
        format_int = format_int << offset
        bit_masks.append(format_int)
        offset += cur_int

    return bit_masks[::-1] #reverse


def truecolor_tga_32_to_txr(stream, tex_params, tgaDebug):

    image_format = tex_params['pfrm']
    has_pfrm = tex_params['has_pfrm']
    gen_mipmap = tex_params['has_lvmp']

    bytes_per_pixel = 4 # 32 bit ARGB

    header = TGAHeader()
    header.from_stream(stream)
    header.id_length = 12 #LOFF declaration
    header.color_map_length = 0 #ColorMapEntrySize
    header.color_map_entry_size = 16 #ColorMapEntrySize
    header.pixel_depht = 16 #PixelDepth
    header.image_descriptor = 32 #Image Descriptor
    width = header.image_width
    height = header.image_height
    colors_size = height*width
    colors_before = stream.read(colors_size*bytes_per_pixel)

    pixels = Image.decode_bytearray_to_pixels(
        bytearray(colors_before), 
        header.image_width,
        header.image_height,
        '8888', 'ARGB'
    )

    img = Image(pixels, header.image_width, header.image_height, 'ARGB', '8888')
    img_bytes = img.save_bytes(image_format, 'ARGB')

    if gen_mipmap:
        mipmaps = generate_mipmaps(bytearray(colors_before), width, height)

    footer = stream.read()

    if tgaDebug:
        debugBuffer = BytesIO()
        debug_header = TGAHeader()
        debug_header.image_type = 2
        debug_header.color_map_entry_size = 16
        debug_header.pixel_depht = 16
        debug_header.image_width = header.image_width
        debug_header.image_height = header.image_height
        debug_header.image_descriptor = 32

        debugBuffer.write(debug_header.to_bytes())
        debugBuffer.write(img_bytes)

    outBuffer = BytesIO()

    loff_ms = outBuffer.tell()
    outBuffer.write(header.to_bytes())
    outBuffer.write('LOFF'.encode('cp1251'))
    outBuffer.write(struct.pack("<i",4))
    loff_write_ms = outBuffer.tell()
    outBuffer.write(struct.pack("<i",0)) #LOFF reserved
    outBuffer.write(img_bytes)
    c.write_size(outBuffer, loff_write_ms, outBuffer.tell() - loff_ms)
    if gen_mipmap and len(mipmaps) > 1:
        outBuffer.write('LVMP'.encode('cp1251'))
        lvmp_write_ms = outBuffer.tell()
        outBuffer.write(struct.pack("<i",0)) #LVMP reserved
        lvmp_ms = outBuffer.tell()
        outBuffer.write(struct.pack("<i", len(mipmaps)-1))
        outBuffer.write(struct.pack("<i", mipmaps[1]['h']))
        outBuffer.write(struct.pack("<i", mipmaps[1]['w']))
        outBuffer.write(struct.pack("<i", 2))

        for m in range(1, len(mipmaps)):
            mipmap = mipmaps[m]['data']
            m_width = mipmaps[m]['w'] # len(mipmap)
            m_height = mipmaps[m]['h'] # len(mipmap[0])
            mipmap_bytearray = bytearray(m_height * m_width * 4)
            for x in range(m_width):
                for y in range(m_height): #BGRA
                    mipmap_bytearray[(x*m_width+y)*4:(x*m_width+y+1)*4] = struct.pack('>I', \
                        ((mipmap[x][y][0]) << 8) | \
                        ((mipmap[x][y][1]) << 16) | \
                        ((mipmap[x][y][2]) << 24) | \
                        ((mipmap[x][y][3]) << 0)  \
                    )

            mipmap_header = copy.copy(header)
            mipmap_header.id_length = 0
            mipmap_header.image_width = m_width
            mipmap_header.image_height = m_height

            mipmap_pixels = Image.decode_bytearray_to_pixels(
                mipmap_bytearray, 
                mipmap_header.image_width,
                mipmap_header.image_height,
                '8888', 'RGBA'
            )

            img = Image(mipmap_pixels, mipmap_header.image_width, mipmap_header.image_height, 'ARGB', '8888')
            mipmap_bytes = img.save_bytes(image_format, 'ARGB')
            # mipmap_bytes = img.save_bytes('1555', 'ARGB')

            outBuffer.write(mipmap_bytes)
        c.write_size(outBuffer, lvmp_write_ms, outBuffer.tell() - lvmp_ms)
        outBuffer.write(struct.pack("<H", 0)) # allign

    if has_pfrm:
        bit_masks = get_argb_bit_mask(image_format)

        a_msk = bit_masks[0]
        r_msk = bit_masks[1]
        g_msk = bit_masks[2]
        b_msk = bit_masks[3]

        outBuffer.write('PFRM'.encode('cp1251'))
        outBuffer.write(struct.pack('<i', 16))
        outBuffer.write(struct.pack('<i', r_msk))
        outBuffer.write(struct.pack('<i', g_msk))
        outBuffer.write(struct.pack('<i', b_msk))
        outBuffer.write(struct.pack('<i', a_msk))

    outBuffer.write('ENDR'.encode('cp1251'))
    outBuffer.write(struct.pack("<i", 0)) # always int 0

    result = {
        "data": outBuffer,
        "debug_data": debugBuffer if tgaDebug else None
    }

    return result

def tga32_to_msk(stream, msk_params, tgaDebug = False):

    msk_type = msk_params['magic']
    print(msk_type)
    has_pfrm = msk_params['has_pfrm']
    image_format = msk_params['pfrm']

    # bytes_per_pixel = 4 # 32 bit ARGB
    
    if msk_type == 'MS16':
        bytes_per_pixel = 2
    else: #MSKR, MSK8, MASK
        bytes_per_pixel = 1

    header = TGAHeader()
    header.from_stream(stream)
    width = header.image_width
    height = header.image_height
    colors_size = height*width
    colors_before = stream.read(colors_size*4) # 32 bit ARGB
    footer = stream.read()
    
    pixels = Image.decode_bytearray_to_pixels(
        bytearray(colors_before), 
        header.image_width,
        header.image_height,
        '8888', 'ARGB'
    )

    palette = None
    indexes = None
    if bytes_per_pixel == 2:
        palette = [(0,0,0) for _ in range(256)]
    else:
        pal = generate_palette(pixels, width, height)
        palette = pal['palette']
        indexes = pal['indexes']

    if bytes_per_pixel == 2:
        img = Image(pixels, width, height, 'ARGB', '8888')
        new_image_pixels = img.save_as(image_format, 'ARGB')

        compressed_data = compress_rle(new_image_pixels, bytes_per_pixel)
    else:
        compressed_data = compress_rle(indexes, 1)

    packed_palette = b''.join(struct.pack('BBB', *pixel) for pixel in palette)

    if tgaDebug:
        debugBuffer = BytesIO()
        debug_header = TGAHeader()
        if bytes_per_pixel == 2:
            debug_header.image_type = 10
            debug_header.color_map_entry_size = 16
            debug_header.pixel_depht = 16
        else: # bytes_per_pixel == 1
            debug_header.image_type = 9
            debug_header.color_map_type = 1
            debug_header.color_map_length = 256
            debug_header.color_map_entry_size = 24
            debug_header.pixel_depht = 8
        debug_header.image_width = header.image_width
        debug_header.image_height = header.image_height
        debug_header.image_descriptor = 32

        debugBuffer.write(debug_header.to_bytes())
        debugBuffer.write(packed_palette)
        debugBuffer.write(compressed_data)

    outBuffer = BytesIO()

    outBuffer.write(msk_type.encode('cp1251'))
    outBuffer.write(struct.pack("<I", width))
    outBuffer.write(struct.pack("<I", height))
    outBuffer.write(packed_palette)

    outBuffer.write(compressed_data)

    if has_pfrm:
        bit_masks = get_argb_bit_mask(image_format)
        a_msk = bit_masks[0]
        r_msk = bit_masks[1]
        g_msk = bit_masks[2]
        b_msk = bit_masks[3]
        outBuffer.write('PFRM'.encode('cp1251'))
        outBuffer.write(struct.pack('<i', 16))
        outBuffer.write(struct.pack('<i', r_msk))
        outBuffer.write(struct.pack('<i', g_msk))
        outBuffer.write(struct.pack('<i', b_msk))
        outBuffer.write(struct.pack('<i', a_msk))
    # outBuffer.write('ENDR'.encode('cp1251'))
    # outBuffer.write(struct.pack("<i", 0)) # always int 0

    result = {
        "data": outBuffer,
        "debug_data": debugBuffer if tgaDebug else None
    }

    return result


def msk_to_tga32(stream, tgaDebug):
    
    colors_after = []
    magic = stream.read(4).decode('cp1251')
    width = struct.unpack("<H", stream.read(2))[0]
    height = struct.unpack("<H", stream.read(2))[0]
    palette_size = 256
    palette_bytes = stream.read(palette_size*3)
    palette = list(struct.unpack("<"+str(palette_size*3)+"B", palette_bytes))
    palette = [palette[i:i+3] for i in range(0, len(palette), 3)]
    colors_size = width*height

    if magic == 'MS16':
        bytes_per_pixel = 2
    else: #MSKR, MSK8, MASK
        bytes_per_pixel = 1

    rleResult = decompress_rle(stream, width, height, bytes_per_pixel)

    colors = rleResult['data']
    rle_bytes = rleResult['rle_bytes']

    header = TGAHeader()
    header.image_type = 2 #ImageType
    header.color_map_entry_size = 32 #ColorMapEntrySize
    header.image_width = width #Width
    header.image_height = height #Height
    header.pixel_depht = 32 #PixelDepth
    header.image_descriptor = 32 #ImageDescriptor
    
    pfrm = None
    pfrm_set = True
    while True:
        footer_identifier = stream.read(4).decode('cp1251')
        if footer_identifier == 'PFRM':
            footer_size = struct.unpack("<i", stream.read(4))[0]
            pfrm = list(struct.unpack("<4i", stream.read(16)))
            continue

        elif footer_identifier == 'ENDR':
            stream.read(4) # alwas int 0
            continue

        stream.seek(-4, 1)
        break
    
    if pfrm is None:
        # pfrm = [61440, 3840, 240, 15] # 4,4,4,4
        pfrm = [0, 63488, 2016, 31] # 5,6,5,0
        # pfrm = [63488, 1984, 62, 1] # 5,5,5,1
        pfrm_set = False


    transp_color = (0,0,0)
    outBuffer = BytesIO()
    header_pack = header.to_bytes()
    outBuffer.write(header_pack)
    if bytes_per_pixel == 1:
        colors_before = list(colors)
        colors_after = palette_to_colors(palette, colors_before, transp_color)

        colors_pack = struct.pack("<"+str(colors_size*4)+"B", *colors_after)
        outBuffer.write(colors_pack)
    else: # bytes_per_pixel == 2
        
        bit_depth = ''.join(str(bin(x).count('1')) for x in pfrm)

        pixels = Image.decode_bytearray_to_pixels(
            bytearray(colors), 
            header.image_width,
            header.image_height,
            bit_depth, 'ARGB'
        )
        old_image = Image(pixels, header.image_width, header.image_height, 'ARGB', bit_depth)

        new_image_bytes = old_image.save_bytes('8888', 'ARGB')
        outBuffer.write(new_image_bytes)


    if tgaDebug:
        debugBuffer = BytesIO()
        debug_header = TGAHeader()
        if bytes_per_pixel == 2:
            debug_header.image_type = 10
            debug_header.color_map_entry_size = 16
            debug_header.pixel_depht = 16
        else: # bytes_per_pixel == 1
            debug_header.image_type = 9
            debug_header.color_map_type = 1
            debug_header.color_map_length = 256
            debug_header.color_map_entry_size = 24
            debug_header.pixel_depht = 8
        debug_header.image_width = header.image_width
        debug_header.image_height = header.image_height
        debug_header.image_descriptor = 32
        
        debug_palette = palette_bytes
        debug_data = rle_bytes 

        debugBuffer.write(debug_header.to_bytes())
        debugBuffer.write(debug_palette)
        debugBuffer.write(debug_data)

    result = {}
    result["format"] = pfrm
    result["pfrm_set"] = pfrm_set
    result["data"] = outBuffer
    result["debug_data"] = debugBuffer if tgaDebug else None
    result["magic"] = magic
    return result
