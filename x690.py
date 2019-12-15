#! /usr/bin/env python3


import argparse


def decode(x690, depth=0):
    offset = 0

    while offset < len(x690):
        # Identifier
        identifier = x690[offset]
        identifier_len = 1

        tag_class = (identifier & 0b11000000) >> 6
        constructed = bool(identifier & 0b00100000)

        # print(f"{'  '*depth}Tag class: 0x{tag_class:02x}")
        # print(f"{'  '*depth}Constructed: {constructed}")

        tag_num = identifier & 0b00011111
        if tag_num == 0b00011111:
            raise NotImplementedError('Cannot parse long-form tag.')

        offset += identifier_len

        # print(f"{'  '*depth}Tag number: 0x{tag_num:02x}")
        print('  '*depth + tag_info(tag_class, tag_num))

        # Length
        length = x690[offset]
        length_len = 1

        if length & 0b10000000:
            length_lower = length & 0b01111111

            if length_lower == 0:
                raise NotImplementedError('Cannot parse indefinite length.')
                length = -1

            elif length_lower < 0b01111111:
                length_len += length_lower

                length = 0
                for length_octet in x690[offset+1:offset+1+length_lower]:
                    length = length << 8 | length_octet

            elif length_lower == 0b01111111:
                raise ValueError('Reserved length format.')

        offset += length_len

        # print(f"{'  '*depth}Length: 0x{length:02x}")

        # Contents
        contents = x690[offset:offset+length]
        offset += length

        if constructed:
            decode(contents, depth=depth+1)
        else:
            if length == 0:
                pass
            elif tag_num == 0x06:
                print(f"{'  '*depth}  {parse_oid(contents)}")
            elif tag_num == 0x13:
                print(f"{'  '*depth}  ", contents.decode())
            else:
                print(f"{'  '*depth}  ",
                      ' '.join(f"{b:02x}" for b in contents))

    return(None)


def tag_info(tag_class, tag_num):
    tag_classes = (
        'native',
        'application-specific',
        'context-specific',
        'private',
    )
    tag_numbers = (
        'End of content',
        'Boolean',
        'Integer',
        'Bit string',
        'Octet string',
        'Null',
        'Object ID',
        'Object descriptor',
        'External',
        'Real/float',
        'Enum',        # 0x10
        'PDV',
        'UTF-8 string',
        'Relative object ID',
        'Time',
        '! Reserved',  # 0x0F
        'Sequence',
        'Set',
        'Numeric string',
        'Printable string',
        'T61 string',  # 0x20
        'Videotex string',
        'IA5 string',
        'UTC time',
        'Generalized time',
        'Graphic string',
        'Visible string',
        'General string',
        'Universal string',
        'Character string',
        'BMP string',  # 0x30
        'Date',
        'Time of day',
        'Datetime',
        'Duration',
        'OID-IRI',
        'Relative OID-IRI',
    )

    printable_class = tag_classes[tag_class]

    printable_num = f"Unknown type 0x{tag_num:02x}"
    if tag_num < len(tag_numbers):
        printable_num = tag_numbers[tag_num]

    return(f"{printable_num} ({printable_class})")


def parse_oid(octets):
    oid = [octets[0] // 0x40, octets[0] % 0x40]

    offset = 1
    node = 0

    while offset < len(octets):
        octet = octets[offset]
        offset += 1

        node = node << 8 | octet & 0b01111111

        if not octet & 0b10000000:
            oid.append(node)
            node = 0

    return '.'.join(str(node) for node in oid)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='X.609 (basic/canonical/distinguished encoding rules) '
                    'parser')

    parser.add_argument('in_file',
                        help='X.690 file to parse',
                        metavar='in',
                        type=argparse.FileType('rb'))

    args = parser.parse_args()

    x690_bytes = args.in_file.read()
    args.in_file.close()

    print(decode(x690_bytes))
