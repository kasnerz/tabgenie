var table_idx = 0;
var total_examples = 1;
var dataset = window.default_dataset;
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
  var activeCells = $("#tablearea").find(".table-active").map(
    function() { 
      return $(this).attr("cell-idx");
    }).get();

  // no highlighted cells -> send all cells except headers
  if (activeCells.length == 0) {
    activeCells = $("#tablearea").find("td").map(
      function() { 
        return $(this).attr("cell-idx");
      }).get();
  }
  return activeCells;
}

function load_model() {
  $.ajax({
    type: "GET",
    url: `${window.url_prefix}/load_model`,
    data: {
      "model" : "totto"
    },
    // beforeSend: function() {
    //     $("#gen-btn").prop('disabled', true);
    // },
    success: function(data) {
        $("#gen-btn").html('Generate');
        $("#gen-btn").removeClass('disabled');
    }
  })
}

function generate() {
  $("#gen-btn").html("Generating...");
  $("#gen-btn").addClass('disabled');
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
    url: `${window.url_prefix}/generate`,
    data: JSON.stringify(request),
    success: function (data) {
      output = data["out"];

      $("#dataset-spinner").hide();
      $("#model-output").html("<hl>" + output + "</hl>");
      $("#outputarea").show();
      $("#gen-btn").html("Generate");
      $("#gen-btn").removeClass('disabled');
    },
    dataType: "json"
  });
}

function fetch_table(dataset, split, table_idx) {
  $.get(`${window.url_prefix}/table`, {
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

  load_model();
});


