from ..divisions import Division


def test_get():
    wake = Division.get('ocd-division/country:us/state:nc/county:wake')
    assert wake.name == 'Wake County'
    assert wake.name in str(wake)


def test_children():
    us = Division.get('ocd-division/country:us')
    assert len(list(us.children('state'))) == 50
