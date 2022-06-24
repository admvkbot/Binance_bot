<style>
.but {
    width: 50px;
}
</style>
 
<div style="padding-left: 30px">     
<form id="id" method="POST" action="bb.php">
<?php 
    $coins = array("BZRX", "STMX", "SFP", "LIT", "BEL", "BLZ", "SKL", "BTS", "UNFI", "KEEP", "CTK", "LINA", "NKN", "ZZZZ");
    sort($coins);
    foreach ($coins as $coin) {
        print ("<button type=\"submit\" value=\"{$coin}\" name=\"submit\" class=\"but\" onclick=\"window.open('https://www.binance.com/ru/futures/{$coin}USDT');return true;\">{$coin}</button><br><br>\n");
    }
?>
</form>
<form id="id" method="POST" action="bb.php">
<?php
    print ("<input id=\"bb\" type=\"textarea\" name=\"submit\"></input><input type=\"submit\" value=\"Run\" class=\"but\" onclick=\"var bb=document.getElementById('bb').value;window.open('https://www.binance.com/ru/futures/'+bb+'USDT');return true;\"/>");
    
?> 
</form>
<form id="id" method="POST" action="bb.php">
<?php
    print ("<button type=\"submit\" value=\"start\" name=\"c\">Start Price Checker</button> <button type=\"submit\" value=\"stop\" name=\"c\">Stop Price Checker</button><br><br>\n");
    
?> 
</form>
<form id="id" method="POST" action="bb.php">
<?php
    print ("<button type=\"submit\" value=\"start\" name=\"b\">Start Megabuyer</button> <button type=\"submit\" value=\"start2\" name=\"b\">Start Megabuyer 1.5</button> <button type=\"submit\" value=\"stop\" name=\"b\">Stop All</button><br><br>\n");
    
?> 
</form>
</div>       

<?php
if (isset($_POST["submit"])){
    $coin = $_POST["submit"];
    $price = 0;
    $coin = strtoupper($coin);
    print(shell_exec("python3 /home/run/orlovbot/main2.py " . $coin . " " . $price . " &"));
}
if (isset($_POST["c"])){
    $action = $_POST["c"];
    if ($action == 'start') {
        print(shell_exec("python3 /home/run/orlovbot/main_price.py &"));
        //print(shell_exec("python3 /home/run/orlovbot/main_price2.py &"));
    }
    else if ($action == 'stop') {
        print(shell_exec("rm /var/www/html/pipe3"));        
        //print(shell_exec("rm /var/www/html/pipe5"));        
    }
}
if (isset($_POST["b"])){
    $action = $_POST["b"];
    if ($action == 'start') {
        print(shell_exec("rm /var/www/html/pipe4"));        
        print(shell_exec("rm /var/www/html/pipe3"));        
        print(shell_exec("killall python3"));        
        print(shell_exec("python3 /home/run/orlovbot/main_price.py &"));
        print(shell_exec("python3 /home/run/orlovbot/my_price.py &"));
    }
    else if ($action == 'start2') {
        print(shell_exec("rm /var/www/html/pipe4"));        
        print(shell_exec("rm /var/www/html/pipe3"));        
        print(shell_exec("killall python3"));        
        print(shell_exec("python3 /home/run/orlovbot/main_price.py &"));
        print(shell_exec("python3 /home/run/orlovbot/my_price2.py &"));
    }
    else if ($action == 'stop') {
        print(shell_exec("rm /var/www/html/pipe4"));        
        print(shell_exec("rm /var/www/html/pipe3"));        
        print(shell_exec("killall python3"));        
    }
}
?>