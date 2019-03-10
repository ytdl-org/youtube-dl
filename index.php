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
$latest = file_get_contents('latest_version');

echo '<div class="latest">';
echo '<div><a href="latest">Latest</a> (v' . htmlspecialchars($latest) . ') downloads:</div>';
echo '<a href="downloads/latest/youtube-dl">youtube-dl</a> ';
echo '<a href="downloads/latest/youtube-dl.exe">youtube-dl.exe</a> ';
echo '<a href="downloads/latest/youtube-dl-' . htmlspecialchars($latest) . '.tar.gz">youtube-dl-' . htmlspecialchars($latest) . '.tar.gz</a>';
echo '</div>';

?>

See the right for more resources.

<table border="0" id="rgb" style="float: right;">
    <tr><td><a class="button" id="main-homepage" href="http://ytdl-org.github.io/youtube-dl/">Homepage</a></td></tr>
    <tr><td><a class="button" id="g" href="http://ytdl-org.github.io/youtube-dl/download.html">Download instructions</a></td></tr>
    <tr><td><a class="button" id="r" href="http://ytdl-org.github.io/youtube-dl/documentation.html">Documentation</a></td></tr>
	<tr><td><a class="button" id="main-support" href="https://github.com/ytdl-org/youtube-dl/issues/">Support</a></td></tr>
	<tr><td><a class="button" id="y" href="https://github.com/ytdl-org/youtube-dl/">Develop</a></td></tr>
	<tr><td><a class="button" id="b" href="http://ytdl-org.github.io/youtube-dl/about.html">About</a></td></tr>
</table>

</body>
</html>
