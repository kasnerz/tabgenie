var table_idx = 0;
var total_examples = 1;
var dataset = window.default_dataset;
var mode = window.mode;
var split = "dev";
var splitInstance = Split(['#centerpanel', '#rightpanel'], { sizes: [70, 30], gutterSize: 1 });


function mod(n, m) {
  return ((n % m) + m) % m;
}

function nextbtn() {
  gotopage(table_idx + 1);
}

function prevbtn() {
  gotopage(table_idx - 1);
}

function gotobtn() {
  var n = $("#page-input").val();
  gotopage(n);
}

function gotopage(page) {
  table_idx = page;
  table_idx = mod(table_idx, total_examples - 1);

  fetch_table(dataset, split, table_idx);
  $("#page-input").val(table_idx);
}

function get_highlighted_cells() {
  var activeCells = $("#tablearea").find(".table-active").map(
    function () {
      return $(this).attr("cell-idx");
    }).get();

  // no highlighted cells -> send all cells except headers
  if (activeCells.length == 0) {
    activeCells = $("#tablearea").find("td").map(
      function () {
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
      "model": "totto"
    },
    // beforeSend: function() {
    //     $("#gen-btn").prop('disabled', true);
    // },
    success: function (data) {
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
    "cells": cells,
    "dataset": dataset,
    "split": split,
    "table_idx": table_idx
  };

  $.ajax({
    type: "POST",
    contentType: "application/json; charset=utf-8",
    url: `${window.url_prefix}/generate`,
    data: JSON.stringify(request),
    success: function (data) {
      output = data["out"];

      $("#dataset-spinner").hide();
      $("#model-placeholder").html("<hl>" + output + "</hl>");
      // $("#outputarea").show();
      $("#gen-btn").html("Generate");
      $("#gen-btn").removeClass('disabled');
    },
    dataType: "json"
  });
}

function postRequestDownload(url, request) {
  // https://stackoverflow.com/questions/4545311/download-a-file-by-jquery-ajax
  xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function () {
    var a;
    if (xhttp.readyState === 4 && xhttp.status === 200) {
      // Trick for making downloadable link
      a = document.createElement('a');
      a.href = window.URL.createObjectURL(xhttp.response);
      // Give filename you wish to download
      a.download = "file.json";
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();
    }
  };
  // Post data to URL which handles post request
  xhttp.open("POST", `${window.url_prefix}/${url}`);
  xhttp.setRequestHeader("Content-Type", "application/json");
  // You should set responseType as blob for binary responses
  xhttp.responseType = 'blob';
  xhttp.send(JSON.stringify(request));
}


function exportData() {
  $("#exp-btn").html("Exporting...");
  $("#exp-btn").addClass('disabled');
  dataset = $('#dataset-select').val();
  split = $('#split-select').val();

  var request = {
    "dataset": dataset,
    "split": split,
    "table_idx": table_idx
  };

  postRequestDownload("export", request);

  $("#exp-btn").html("Export");
  $("#exp-btn").removeClass('disabled');
}


function parse_info(info) {
  return ("<h3>" + info.name + "</h3><p>" + info.description + "</p>" +
    "<h5>Homepage</h5><p><a href=\"" + info.homepage + "\">" + info.homepage + "</a></p>" +
    "<h5>Citation:</h5><p><code>" + info.citation + "</code></p>")
}

function fetch_table(dataset, split, table_idx) {
  $.get(`${window.url_prefix}/table`, {
    "dataset": dataset,
    "table_idx": table_idx,
    "split": split
  }, function (data) {
    $("#reference-placeholder").html(data.ref);
    $("#reference-checkbox").prop("checked", true);
    $("#tablearea").html(data.html);
    $("#export-placeholder").text(JSON.stringify(data.export, null, 4));
    console.log(JSON.stringify(data.export, null, 4));
    $("#dataset-spinner").hide();
    total_examples = data.total_examples;
    info = parse_info(data.dataset_info);

    ["th", "td"].forEach(
      function (celltype) {
        var cells = $("#tablearea").find(celltype);
        cells.on("click",
          function () {
            $(this).toggleClass("table-active");
          }
        );
        $("#tablearea").addClass("interactive-cell");
      }
    );
    $("#dataset-info").html(info);
  });
  $("#model-placeholder").html();
  // $("#outputarea").hide();
}


$('#reference-checkbox').on('change', function () {
  if (!this.checked) {
    $("#reference-output").hide();
  } else {
    $("#reference-output").show();
  }
});

$('#panel-checkbox').on('change', function () {
  if ($('#rightpanel').hasClass("show")) {
    splitInstance.collapse(1);
    $('#tabulararea').css("overflow-x", "auto");
    $('.gutter').hide();
  } else {
    splitInstance.setSizes([70, 30])
    $('#tabulararea').css("overflow-x", "scroll");
    $('.gutter').show();
  }
  $('#rightpanel').collapse("toggle");

});

$("#dataset-select").on("change", function (e) {
  $("#dataset-spinner").show();
  dataset = $('#dataset-select').val();
  table_idx = 0;
  fetch_table(dataset, split, table_idx);
  $("#page-input").val(table_idx);
});


$("#split-select").on("change", function (e) {
  $("#dataset-spinner").show();
  split = $('#split-select').val();
  table_idx = 0;
  fetch_table(dataset, split, table_idx);
  $("#page-input").val(table_idx);
});


$('#page-input').keypress(function (event) {
  if (event.keyCode == 13) {
    gotobtn();
  }
});


$(document).ready(function () {
  $("#dataset-select").val(dataset).change();

  fetch_table(dataset, split, table_idx);
  $("#page-input").val(table_idx);

  if (mode != "light") {
    load_model();
  }
});
