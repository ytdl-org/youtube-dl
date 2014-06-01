<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-type" content="text/html;charset=UTF-8">
<title>youtube-dl</title>
<link rel="stylesheet" href="style.css" type="text/css">
</head>
<body>

<h1>youtube-dl downloads</h1>

<?php
$DOWNLOAD_DIR = 'downloads';

$versions = array_filter(scandir($DOWNLOAD_DIR), function($v) {return (($v{0} != '.') && ($v != 'latest'));});
sort($versions);

$latest = end($versions);

echo '<div class="latest">';
echo '<div><a href="latest">Latest</a> (v' . htmlspecialchars($latest) . ') downloads:</div>';
echo '<a href="downloads/' . htmlspecialchars($latest) . '/youtube-dl">youtube-dl</a> ';
echo '<a href="downloads/' . htmlspecialchars($latest) . '/youtube-dl.exe">youtube-dl.exe</a> ';
echo '<a href="downloads/' . htmlspecialchars($latest) . '/youtube-dl-' . htmlspecialchars($latest) . '.tar.gz">youtube-dl-' . htmlspecialchars($latest) . '.tar.gz</a>';
echo '</div>';

echo '<ul class="all-versions">';
foreach ($versions as $version) {
    echo '<li><a href="downloads/' . htmlspecialchars($version) . '">' . htmlspecialchars($version) . '</a></li>';
}
echo '</ul>';

?>


<table border="0" id="rgb" style="float: right;">
    <tr><td><a class="button" id="main-homepage" href="http://rg3.github.com/youtube-dl/">Homepage</a></td></tr>
    <tr><td><a class="button" id="g" href="http://rg3.github.com/youtube-dl/download.html">Download instructions</a></td></tr>
    <tr><td><a class="button" id="r" href="http://rg3.github.com/youtube-dl/documentation.html">Documentation</a></td></tr>
	<tr><td><a class="button" id="main-support" href="https://github.com/rg3/youtube-dl/issues/new">Support</a></td></tr>
	<tr><td><a class="button" id="y" href="https://github.com/rg3/youtube-dl/">Develop</a></td></tr>
	<tr><td><a class="button" id="b" href="http://rg3.github.com/youtube-dl/about.html">About</a></td></tr>
</table>

</body>
</html>
