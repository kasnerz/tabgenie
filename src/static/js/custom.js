var table_idx = 0;
var total_examples = 1;
var dataset = window.default_dataset;
var mode = window.mode;
var pipelines = window.pipelines;
var preloaded_outputs = window.preloaded_outputs;
var url_prefix = window.location.href.split('#')[0];
var split = "dev";


function update_svg_width() {
  w = $("#svg-body").width();
  svg.attr("width", w);
}

var splitInstance = Split(['#centerpanel', '#rightpanel'], {
  sizes: [70, 30], onDragEnd: function () { update_svg_width }, gutterSize: 1
});

function randint(max) {
  return Math.floor(Math.random() * max);
}

function mod(n, m) {
  return ((n % m) + m) % m;
}

function nextbtn() {
  gotopage(table_idx + 1);
}

function prevbtn() {
  gotopage(table_idx - 1);
}

function startbtn() {
  gotopage(0);
}

function endbtn() {
  gotopage(total_examples - 1);
}

function randombtn() {
  gotopage(randint(total_examples - 1));
}

function gotobtn() {
  var n = $("#page-input").val();
  gotopage(n);
}

function gotopage(page) {
  table_idx = page;
  table_idx = mod(table_idx, total_examples);

  fetch_table(dataset, split, table_idx);
  $("#page-input").val(table_idx);
}

function format_info(info) {
  return ("<h3>" + info.name + "</h3><p>" + info.description + "</p>" +
    "<h5>Homepage</h5><p><a href=\"" + info.homepage + "\">" + info.homepage + "</a></p>" +
    "<h5>Citation:</h5><p><code>" + info.citation + "</code></p>")
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

function is_pipeline_active(pipeline) {
  return $(`#out-${pipeline}`).length > 0;
}

function has_pipeline_content(pipeline) {
  return get_pipeline_placeholder(pipeline).text() !== "";
}

function get_pipeline_placeholder(pipeline) {
  if (!is_pipeline_active(pipeline)) {
    $("#outputarea").append(`<div class="pipeline-output" id="out-${pipeline}">
    <label>${pipeline}</label>
    <div id="out-${pipeline}-placeholder" class="font-mono"></div>
    </div>`);
  }
  return $(`#out-${pipeline}-placeholder`);
}

function remove_pipeline_placeholder(pipeline) {
  $(`#out-${pipeline}`).remove();
}
function set_pipeline_output(pipeline, output) {
  var placeholder = get_pipeline_placeholder(pipeline);
  placeholder.html(output);
}
function erase_pipeline_output(pipeline) {
  if (is_pipeline_active(pipeline)) {
    set_pipeline_output(pipeline, "");
  }
}

function reset_pipeline_outputs() {
  for (var pipeline in pipelines) {
    erase_pipeline_output(pipeline);
  }
}

function run_pipeline(pipeline) {
  cells = get_highlighted_cells();
  dataset = $('#dataset-select').val();
  split = $('#split-select').val();

  var request = {
    "pipeline": pipeline,
    "dataset": dataset,
    "split": split,
    "table_idx": table_idx,
    "cells": cells
  };

  $.ajax({
    type: "POST",
    contentType: "application/json; charset=utf-8",
    url: `${url_prefix}/pipeline`,
    data: JSON.stringify(request),
    success: function (data) {
      output = data["out"];
      // $("#dataset-spinner").hide();
      set_pipeline_output(pipeline, output);
    },
    dataType: "json"
  });
}

function reload_pipelines() {
  reset_pipeline_outputs();
  for (var pipeline in pipelines) {
    if (pipelines[pipeline].active) {
      run_pipeline(pipeline);
    }
  }
}

function postRequestDownload(url, request, filename) {
  // https://stackoverflow.com/questions/4545311/download-a-file-by-jquery-ajax
  xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function () {
    var a;
    if (xhttp.readyState === 4 && xhttp.status === 200) {
      // Trick for making downloadable link
      a = document.createElement('a');
      a.href = window.URL.createObjectURL(xhttp.response);
      // Give filename you wish to download
      a.download = filename;
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


function export_table(format) {
  $("#exp-btn").html("Exporting...");
  $("#exp-btn").addClass('disabled');
  dataset = $('#dataset-select').val();
  split = $('#split-select').val();

  var request = {
    "dataset": dataset,
    "split": split,
    "table_idx": table_idx,
    "format": format
  };
  var filename = `${dataset}_${split}_tab_${table_idx}.${format}`;

  postRequestDownload("export_table", request, filename);

  $("#exp-btn").html("Export");
  $("#exp-btn").removeClass('disabled');
}


function fetch_table(dataset, split, table_idx, export_format) {
  $.get(`${url_prefix}/table`, {
    "dataset": dataset,
    "table_idx": table_idx,
    "split": split,
    "pipelines": JSON.stringify(pipelines)
  }, function (data) {
    reset_pipeline_outputs();
    $("#tablearea").html(data.html);
    $("#dataset-spinner").hide();
    total_examples = data.total_examples;
    info = format_info(data.dataset_info);

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

    for (var pipeline_out of data.pipeline_outputs) {
      set_pipeline_output(pipeline_out["pipeline_name"], pipeline_out["out"]);
    }
    for (var generated_out of data.generated_outputs) {
      set_pipeline_output(generated_out["name"], generated_out["out"]);
    }

    for (var pipeline in pipelines) {
      if (pipelines[pipeline].active && !has_pipeline_content(pipeline)) {
        run_pipeline(pipeline);
      }
    }
  });
}

$('.pipeline-checkbox').on('change', function () {
  pipeline_name = $(this)[0].id;
  var pipeline_name = $(`label[for='${pipeline_name}']`).text();

  state = pipelines[pipeline_name].active;

  if (state == 1) {
    remove_pipeline_placeholder(pipeline_name);
    pipelines[pipeline_name].active = 0
  } else {
    run_pipeline(pipeline_name);
    pipelines[pipeline_name].active = 1;
  }
});

$('#table-checkbox').on('change', function () {
  if ($('#centerpanel').hasClass("show")) {
    splitInstance.collapse(0);
    // $('#tabulararea').css("overflow-x", "auto");
    $('.gutter').hide();
  } else {
    splitInstance.setSizes([70, 30])
    // $('#tabulararea').css("overflow-x", "scroll");
    $('.gutter').show();
  }
  update_svg_width();
  $('#centerpanel').collapse("toggle");
});

$('#panel-checkbox').on('change', function () {
  if ($('#rightpanel').hasClass("show")) {
    splitInstance.collapse(1);
    // $('#tabulararea').css("overflow-x", "auto");
    $('.gutter').hide();
  } else {
    splitInstance.setSizes([70, 30])
    // $('#tabulararea').css("overflow-x", "scroll");
    $('.gutter').show();
  }
  update_svg_width();
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

$("#format-select").on("change", function (e) {
  $("#dataset-spinner").show();
  console.log("on format select");
  fetch_table(dataset, split, table_idx);
});


$('#page-input').keypress(function (event) {
  // Enter = Go to page
  if (event.keyCode == 13) {
    gotobtn();
  }
});

$(document).ready(function () {
  $("#dataset-select").val(dataset).change();
  $("#page-input").val(table_idx);
});
