
tests = [
    {
        'code': '''
            var MAX_LENGTH = 0xffffffff;

            var a = {};
            a.length = MAX_LENGTH + 1;
            assertEq([].unshift.call(a), MAX_LENGTH);
            assertEq(a.length, MAX_LENGTH);

            function testGetSet(len, expected) {
                var newlen;
                var a = { get length() { return len; }, set length(v) { newlen = v; } };
                var res = [].unshift.call(a);
                assertEq(res, expected);
                assertEq(newlen, expected);
            }

            testGetSet(0, 0);
            testGetSet(10, 10);
            testGetSet("1", 1);
            testGetSet(null, 0);
            testGetSet(MAX_LENGTH + 2, MAX_LENGTH);
            testGetSet(-5, 0);
            '''
    }
]
