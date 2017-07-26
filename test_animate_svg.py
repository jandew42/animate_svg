import animate, pytest

def test_xpath():
    root = animate.cairosvg.parser.Tree(url='test.svg')
    for child in root.children:
        xpath = animate.Transition.get_xpath(child)
        assert child == animate.Transition.xpath(root, xpath)
        
path_str = """M 859.671,771.355 H 841.67 v 748.999
    S 839.346, 730.648 836.955 718.695
    q 832.702 ,697.43 823.222 , 668.619
    t 827.662 646.418
    a 829.483 637.316 830.848 627.991 831.793 618.539 833.073
    M 605.734 833.84 l 582.418 843.151 h 573.107
    C 1047.499 681.46 1038.434 725.79 1022.813 741.411
    998.789 765.435 962.584 781.68 928.852 781.68
    922.89 781.68 911.683 783.899 906.136 781.68
    897.622 778.275 887.317 779.815 878.257 777.55
    873.265 776.302 866.876 771.355 863.802 771.355
    L 859.671 771.355 Z"""

path_data = [('M', 859.671, 771.355), ('H', 841.67), ('v', 748.999),
    ('S', 839.346, 730.648, 836.955, 718.695),
    ('q', 832.702, 697.43, 823.222, 668.619),
    ('t', 827.662, 646.418),
    ('a', 829.483, 637.316, 830.848, 627.991, 831.793, 618.539, 833.073),
    ('M', 605.734, 833.84), ('l', 582.418, 843.151), ('h', 573.107),
    ('C', 1047.499, 681.46, 1038.434, 725.79, 1022.813, 741.411),
    ('C', 998.789, 765.435, 962.584, 781.68, 928.852, 781.68),
    ('C', 922.89, 781.68, 911.683, 783.899, 906.136, 781.68),
    ('C', 897.622, 778.275, 887.317, 779.815, 878.257, 777.55),
    ('C', 873.265, 776.302, 866.876, 771.355, 863.802, 771.355),
    ('L', 859.671, 771.355), ('Z')]

def test_path_str_to_data():
    assert path_data == \
        animate.Transition.path_str_to_data(animate.Transition, path_str)

def test_path_data_to_str():
    assert path_data == \
        animate.Transition.path_str_to_data(animate.Transition,
            animate.Transition.path_data_to_str(animate.Transition, path_data))

def test_bijects():
    filenames = sorted(animate.glob.glob("plaininkhand*.svg"))
    trans = animate.Transition(filenames)
    assert trans.bijects == [{0: 0, 1: 1, 2: 2}, {0: 0, 1: 2, 2: 1}]

    filenames = sorted(animate.glob.glob("breakhand*.svg"))
    with pytest.raises(ValueError):
        trans = animate.Transition(filenames)

def test_check_tag_path():
    """
    This test seems like it'll be really tedious to create.
    """
    pass

