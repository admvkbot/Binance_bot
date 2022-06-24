<?php
$coin = $_GET['c'];
$price = $_GET['p'];
//print ($coin.$price);
if ($coin && $price)
    print(shell_exec("python3 /home/run/orlovbot/main.py " . $coin . " " . $price . " &"));
?>