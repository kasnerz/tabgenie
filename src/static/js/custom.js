var table_idx = 0;
var total_examples = 1;
// var dataset = "totto";
var dataset = "webnlg";
var split = "dev";

function mod(n, m) {
  return ((n % m) + m) % m;
}

function nextbtn(){
  gotopage(table_idx+1);
}

function prevbtn(){
  gotopage(table_idx-1);
}

function gotobtn(){
  var n = $("#page-input").val();
  gotopage(n);
}

function gotopage(page){
  table_idx = page;
  table_idx = mod(table_idx, total_examples - 1);

  fetch_table(dataset, split, table_idx);
  $("#page-input").val(table_idx);
}

function get_highlighted_cells() {
  var activeCells = $("#tablearea").find("td.table-active").map(
    function() { 
      return $(this).text();
    }).get();
  return activeCells;
}

function load_model() {
  $.ajax({
    type: "GET",
    url: "/load_model",
    data: {
      "model" : "webnlg"
    },
    beforeSend: function() {
        $("#model-spinner").show();
    },
    success: function(data) {
        $("#model-spinner").hide();
        $("#gen-btn").show();
    }
  })
}

function generate() {
  cells = get_highlighted_cells();
  dataset = $('#dataset-select').val();
  split = $('#split-select').val();

  var request = {
    "cells" : cells,
    "dataset" : dataset,
    "split" : split,
    "table_idx" : table_idx
  };

  $.ajax({
    type: "POST",
    contentType: "application/json; charset=utf-8",
    url: "/generate",
    data: JSON.stringify(request),
    success: function (data) {
      output = data["out"];

      $("#dataset-spinner").hide();
      $("#model-output").html("<hl>" + output + "</hl>");
      $("#outputarea").show();
    },
    dataType: "json"
  });
}

function fetch_table(dataset, split, table_idx) {
  $.get("/table", {
    "dataset" : dataset,
    "table_idx" : table_idx,
    "split" : split
  }, function(data) {
      $("#reference").html( data.ref );
      $("#tablearea").html( data.html );
      $("#dataset-spinner").hide();
      total_examples = data.total_examples;

      ["th", "td"].forEach(
        function (celltype) {
          var cells = $("#tablearea").find(celltype);
          cells.on("click",
            function() {
              $(this).toggleClass("table-active");
              }
          );
          $("#tablearea").addClass("interactive-cell");
        }
      );
    });
  $("#model-output").html();
  $("#outputarea").hide();
}

$("#dataset-select").on("change", function(e) {
  $("#dataset-spinner").show();
  dataset = $('#dataset-select').val();
  table_idx = 0;
  fetch_table(dataset, split, table_idx);
  $("#page-input").val(table_idx);
});


$("#split-select").on("change", function(e) {
  $("#dataset-spinner").show();
  split = $('#split-select').val();
  table_idx = 0;
  fetch_table(dataset, split, table_idx);
  $("#page-input").val(table_idx);
});


$('#page-input').keypress(function(event) {
  if (event.keyCode == 13) {
      gotobtn();
  }
});


$( document ).ready(function() {
  $("#dataset-select").val(dataset).change();

  fetch_table(dataset, split, table_idx);
  $("#page-input").val(table_idx);

  // load_model();
});


