Describe 'Flake8' {
    It 'Does not return any errors' {
        & flake8 /Users/jhoek/GitHub/youtube-dl/youtube_dl/extractor/npo.py | Should BeNullOrEmpty
    }
}

Describe 'Tests' {
    It 'Should work in Python 2.6' {
        & 'python2.6' '--version' 2>&1 | Should Be 'Python 2.6.9'

        '', '_1', '_2' | ForEach-Object {
            & 'python2.6' /Users/jhoek/GitHub/youtube-dl/test/test_download.py "TestDownload.test_NPORecents$($_)" 2>&1 
            $LASTEXITCODE | Should Be 0
        }
    }

    It 'Should work in Python 2.7' {
        & python '--version' 2>&1 | Should Be 'Python 2.7.13'

        '', '_1', '_2' | ForEach-Object {
            & python /Users/jhoek/GitHub/youtube-dl/test/test_download.py "TestDownload.test_NPORecents$($_)" 2>&1 
            $LASTEXITCODE | Should Be 0
        }
    }

    It 'Should work in Python 3.5' {
        & python3 '--version' | Should Be 'Python 3.5.2'

        '', '_1', '_2' | ForEach-Object {
            & python3 /Users/jhoek/GitHub/youtube-dl/test/test_download.py "TestDownload.test_NPORecents$($_)" 2>&1 
            $LASTEXITCODE | Should Be 0
        }
    }

    It 'Should work in Python 3.6' {
        & python3.6 '--version' | Should Be 'Python 3.6.1'

        '', '_1', '_2' | ForEach-Object {
            & 'python3.6' /Users/jhoek/GitHub/youtube-dl/test/test_download.py "TestDownload.test_NPORecents$($_)" 2>&1 
            $LASTEXITCODE | Should Be 0
        }
    }
}
