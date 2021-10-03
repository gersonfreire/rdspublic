

"""
Integração https://panel.capiwha.com/
gmail
"""

# //https://panel.capiwha.com/page_api.php
# //http://panel.capiwha.com/get_messages.php?apikey=Z649BSLUYPUUPHKNA6CM&number=5526996080357&type=IN&markaspulled=1&getnotpulledonly=1

"""
// Exemplo de obter mensagens PHP
//http://panel.capiwha.com/get_messages.php?apikey=Z649BSLUYPUUPHKNA6CM&number=5526996080357&type=IN&markaspulled=1&getnotpulledonly=1

$my_apikey = "Z649BSLUYPUUPHKNA6CM"; //"THE NUMBER'S APIKEY";
$number = "5526996080357";//"DESTINATION";
$type = "IN";//"TYPE OF MESSAGE: IN or OUT";
$markaspulled = "1";//"1 or 0";
$getnotpulledonly = "0";//"1 or 0";
        
$api_url  = "http://panel.capiwha.com/get_messages.php";
$api_url .= "?apikey=". urlencode ($my_apikey);
$api_url .= "&number=". urlencode ($number);
$api_url .= "&type=". urlencode ($type);
$api_url .= "&markaspulled=". urlencode ($markaspulled);
$api_url .= "&getnotpulledonly=". urlencode ($getnotpulledonly);
$my_json_result = file_get_contents($api_url, false);
$my_php_arr = json_decode($my_json_result);
foreach($my_php_arr as $item)
{
  $from_temp = $item->from;
  $to_temp = $item->to;
  $text_temp = $item->text;
  $type_temp = $item->type;
  echo "<br>". $from_temp ." -> ". $to_temp ." (". $type_temp ."): ". $text_temp;
  // Do something
}

"""