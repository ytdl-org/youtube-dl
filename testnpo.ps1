Clear-host

$Urls = @{}
$Urls.Add('keuringsdienst', 'https://www.npo.nl/keuringsdienst-van-waarde/KN_1678993/search?category=broadcasts&page=1')
$Urls.Add('jinek', 'https://www.npo.nl/jinek/KN_1676589/search?media_type=broadcast&start=0&rows=8')
$Urls.Add('midsomer', 'https://www.npo.nl/midsomer-murders/POW_00828660/search?media_type=broadcast&start=0&rows=8')
$Urls.Add('pownews', 'https://www.npo.nl/pownews-flits/POW_03469040/search?category=broadcasts&page=1')

$Urls.GetEnumerator() | ForEach-Object {
    Write-Host $_.Key

    $response = Invoke-WebRequest -Uri ($_.Value) -UseBasicParsing -OutFile "~/Desktop/$($_.Key).txt"
}