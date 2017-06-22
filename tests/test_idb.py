from fixtures import *

import logging
import binascii


#logging.basicConfig(level=logging.DEBUG)


def test_validate(empty_idb, kernel32_idb):
    # should be no ValueErrors here.
    assert empty_idb.validate() is True
    assert kernel32_idb.validate() is True


def test_header(empty_idb):
    assert empty_idb.header.signature == b'IDA1'
    assert empty_idb.header.sig2 == 0xAABBCCDD


def test_id0(kernel32_idb):
    assert kernel32_idb.id0.next_free_offset == 0x30
    assert kernel32_idb.id0.page_size == 0x2000
    assert kernel32_idb.id0.root_page == 0x1
    assert kernel32_idb.id0.record_count == 0x6735b
    assert kernel32_idb.id0.page_count == 0x638

    p1 = kernel32_idb.id0.get_page(0x1)
    for entry in p1.get_entries():
        assert entry.key is not None

    p1.validate()


def test_find_exact_match(kernel32_idb):
    # this is found in the root node, first index
    key = binascii.unhexlify('2e6892663778689c4fb7')
    assert binascii.hexlify(kernel32_idb.id0.find(key).key) == binascii.hexlify(key)
    assert binascii.hexlify(kernel32_idb.id0.find(key).value) == b'13'

    # this is found in the second level, third index
    key = binascii.unhexlify('2e689017765300000009')
    assert binascii.hexlify(kernel32_idb.id0.find(key).key) == binascii.hexlify(key)
    assert binascii.hexlify(kernel32_idb.id0.find(key).value) == b'02'

    # this is found in the root node, last index.
    key = binascii.unhexlify('2eff001bc44e')
    assert binascii.hexlify(kernel32_idb.id0.find(key).key) == binascii.hexlify(key)
    assert binascii.hexlify(kernel32_idb.id0.find(key).value) == b'24204636383931344133462e6c705375624b6579'

    # this is found on a leaf node, first index
    key = binascii.unhexlify('2e6890142c5300001000')
    assert binascii.hexlify(kernel32_idb.id0.find(key).key) == binascii.hexlify(key)
    assert binascii.hexlify(kernel32_idb.id0.find(key).value) == b'01080709'

    # this is found on a leaf node, fourth index
    key = binascii.unhexlify('2e689a288c530000000a')
    assert binascii.hexlify(kernel32_idb.id0.find(key).key) == binascii.hexlify(key)
    assert binascii.hexlify(kernel32_idb.id0.find(key).value) == b'02'

    # this is found on a leaf node, last index
    key = binascii.unhexlify('2e6890157f5300000009')
    assert binascii.hexlify(kernel32_idb.id0.find(key).key) == binascii.hexlify(key)
    assert binascii.hexlify(kernel32_idb.id0.find(key).value) == b'02'

    # exercise the max/min range
    minkey = binascii.unhexlify('24204d4158204c494e4b')
    assert binascii.hexlify(kernel32_idb.id0.find(minkey).key) == binascii.hexlify(minkey)

    maxkey = binascii.unhexlify('4e776373737472')
    assert binascii.hexlify(kernel32_idb.id0.find(maxkey).key) == binascii.hexlify(maxkey)


def test_cursor_easy_leaf(kernel32_idb):
    # this is found on a leaf, second to last index.
    # here's the surrounding layout:
    #
    #      00:00: 2eff00002253689cc95b = ff689cc95b40ff8000c00bd30201
    #    > 00:01: 2eff00002253689cc99b = ff689cc99b32ff8000c00be35101
    #      00:00: 2eff00002253689cc9cd = ff689cc9cd2bff8000c00be12f01
    key = binascii.unhexlify('2eff00002253689cc99b')
    cursor = kernel32_idb.id0.find(key)

    cursor.next()
    assert binascii.hexlify(cursor.key) == b'2eff00002253689cc9cd'

    cursor.prev()
    cursor.prev()
    assert binascii.hexlify(cursor.key) == b'2eff00002253689cc95b'


def test_cursor_branch(kernel32_idb):
    #   576 contents (branch):
    #     ...
    #     000638: 2eff00002253689b9535 = ff689b953573ff441098aa0c040c16000000000000
    #   > 000639: 2eff00002253689bea8e = ff689bea8e8257ff8000c00aa2c601
    #     00000e: 2eff00002253689ccaf1 = ff689ccaf113ff8000c00be25301
    #     ...
    #
    #   638 contents (leaf):
    #     00:00: 2eff00002253689b95db = ff689b95db54ff441098ad08040c14000000000000
    #     00:01: 2eff00002253689b9665 = ff689b96655bff441098b008040815000000000000
    #     00:00: 2eff00002253689b970f = ff689b970f808bff441098b30804141f000000000000
    #     ...
    #     00:01: 2eff00002253689be79b = ff689be79b1bff8000c00a9d4b01
    #     00:00: 2eff00002253689be7b6 = ff689be7b68270ff8000c00af6a101
    #   > 00:00: 2eff00002253689bea26 = ff689bea2668ff8000c00a9f4301
    #
    #
    #   639 contents (leaf):
    #   > 00:00: 2eff00002253689bece5 = ff689bece514ff8000c00bc6b701
    #     00:00: 2eff00002253689becf9 = ff689becf942ff8000c008cf9e01
    #     00:00: 2eff00002253689bed3b = ff689bed3b42ff8000c0090b9c01
    #     ...
    #     00:00: 2eff00002253689cc95b = ff689cc95b40ff8000c00bd30201
    #     00:01: 2eff00002253689cc99b = ff689cc99b32ff8000c00be35101
    #     00:00: 2eff00002253689cc9cd = ff689cc9cd2bff8000c00be12f01

    key = binascii.unhexlify('2eff00002253689bea8e')
    cursor = kernel32_idb.id0.find(key)
    cursor.next()
    assert binascii.hexlify(cursor.key) == b'2eff00002253689bece5'

    key = binascii.unhexlify('2eff00002253689bea8e')
    cursor = kernel32_idb.id0.find(key)
    cursor.prev()
    assert binascii.hexlify(cursor.key) == b'2eff00002253689bea26'


def test_cursor_min_max(kernel32_idb):
    # test cursor movement from min and max keys
    # min leaf key: 24204d4158204c494e4b
    # max leaf key: 4e776373737472
    pass


def test_id1(kernel32_idb):
    segments = kernel32_idb.id1.segments
    # collected empirically
    assert len(segments) == 2
    for segment in segments:
        assert segment.bounds.start < segment.bounds.end
    assert segments[0].bounds.start == 0x68901000
    assert segments[1].bounds.start == 0x689DD000

    id1 = kernel32_idb.id1
    assert id1.get_segment(0x68901000).bounds.start == 0x68901000
    assert id1.get_segment(0x68901001).bounds.start == 0x68901000
    assert id1.get_segment(0x689dc000 - 1).bounds.start == 0x68901000
    assert id1.get_next_segment(0x68901000).bounds.start == 0x689DD000
    assert id1.get_flags(0x68901000) == 0x2590
    assert id1.get_byte(0x68901000) == 0x90


def test_nam(kernel32_idb):
    names = kernel32_idb.nam.names()
    # collected empirically
    assert len(names) == 14252
    assert names[0] == 0x68901010
    assert names[-1] == 0x689DE228