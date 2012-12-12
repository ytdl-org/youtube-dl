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

$versions = array_filter(function($v) {return $v{0} != '.'}, scandir($DOWNLOAD_DIR));
sort($versions);

$latest = end($versions);

echo '<div class="latest">';
echo '<div>Latest (v' . htmlspecialchars($latest) . ') downloads:</div>';
echo '<a href="' . htmlspecialchars($latest) . '/youtube-dl">youtube-dl</a> ';
echo '<a href="' . htmlspecialchars($latest) . '/youtube-dl.exe">youtube-dl.exe</a> ';
echo '<a href="' . htmlspecialchars($latest) . '/youtube-dl-src-' . htmlspecialchars($latest) . '.tar.gz">youtube-dl-src-' . htmlspecialchars($latest) . '.tar.gz</a>';
echo '</div>';

echo '<ul>';
foreach ($versions as $v) {
    echo '<li><a href="' . htmlspecialchars($version) . '">' . htmlspecialchars($version) . '</a></li>';
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

<div class="note">
<a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/3.0/">
<img alt="Creative Commons License" style="border-width:0"
src="http://i.creativecommons.org/l/by-nc-sa/3.0/80x15.png" /></a><br />
Copyright © 2006-2012 Ricardo Garcia Gonzalez</div>
</body>
</html>
