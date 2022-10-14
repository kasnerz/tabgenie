function nextbtn(){
  var idx =  get_current_idx() + 1;
  fetch_table(idx);
}

function prevbtn(){
  var idx =  get_current_idx() - 1;
  fetch_table(idx);
}

function get_current_idx(){
  return parseInt($("#page-btn")[0].text, 10);
}

function fetch_table(table_idx) {
  $.get("/table", { i: table_idx }, function(data) {
      $("#reference").html( data.ref );
      $("#tablearea").html( data.html );
    });
  $("#page-btn").html(table_idx);
}

$( document ).ready(function() {
  var idx =  get_current_idx();
  fetch_table(idx);
});