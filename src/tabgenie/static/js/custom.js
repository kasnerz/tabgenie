var table_idx = 0;
var total_examples = 1;
var dataset = window.default_dataset;
var pipelines = window.pipelines;
var generated_outputs = window.generated_outputs;
var url_prefix = window.location.href.split('#')[0];
var split = "dev";
var mode = "highlight";
var editedCells = {};
var favourites = {};


function update_svg_width() {
  if (typeof svg != "undefined") {
    w = $("#svg-body").width();
    svg.attr("width", w);
  }
}

// the draggable divider between the main area and the right panel 
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

function favouritebtn() {
  var favourite_id = `${dataset}-${split}-${table_idx}`;

  if (favourite_id in favourites) {
    remove_favourite(favourite_id);
    return;
  }
  favourites[favourite_id] = { "dataset": dataset, "split": split, "table_idx": table_idx };

  update_favourite_button();

  $("#favourites-area").attr("hidden", false);
  $("#option-export-favourites").removeAttr("disabled");

  var btn_remove = $("<button></button>")
    .attr("type", "button")
    .css("width", "0.5em !important")
    .addClass("btn")
    .attr("onclick", `remove_favourite('${favourite_id}');`)
    .text("✕");

  var span_el = $("<span></span>")
    .addClass("clickable")
    .text(`${favourite_id}`)
    .attr("onclick", `gotoexample('${dataset}', '${split}', '${table_idx}');`);

  span_el.append(btn_remove);

  var li_el = $("<li></li>")
    .addClass("list-group-item")
    .attr("id", `fav-${favourite_id}`);

  li_el.append(span_el);

  $("#favourites-box").append(li_el);
}

function remove_favourite(favourite) {
  delete favourites[favourite];
  $(`#fav-${favourite}`).remove();
  update_favourite_button();

  if ($.isEmptyObject(favourites)) {
    $("#favourites-area").attr("hidden", true);
    $("#option-export-favourites").prop("disabled", true);
    $("#option-export-favourites").prop("checked", false);
    $("#option-export-table").prop("checked", true);
  }
}

function gotobtn() {
  var n = $("#page-input").val();
  gotopage(n);
}

function gotoexample(dataset, split, table_idx) {
  $('#dataset-select').val(dataset);
  $('#split-select').val(split);
  change_split();
  gotopage(table_idx);
}

function gotopage(page) {
  table_idx = page;
  table_idx = mod(table_idx, total_examples);

  fetch_table(dataset, split, table_idx);
  $("#page-input").val(table_idx);
}

function set_dataset_info(info) {
  $("#dataset-info").html("<h3>" + info.name + "</h3><p>" + info.description + "</p>" +
    "<h5>Homepage</h5><p><a href=\"" + info.homepage + "\">" + info.homepage + "</a></p>" +
    "<h5>Citation:</h5><p><code>" + info.citation + "</code></p>");
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

function set_output(name, output) {
  // TODO don't set output on disabled outputs
  var placeholder = $(`#out-${name}-placeholder`);
  placeholder.html(output);
}

function reset_pipeline_outputs() {
  for (var pipeline in pipelines) {
    set_output(pipeline, "");
  }
}
function reset_edited_cells() {
  editedCells = {};
}

function run_pipeline(pipeline) {
  cells = get_highlighted_cells();
  dataset = $('#dataset-select').val();
  split = $('#split-select').val();
  custom_input = $('#model-api-textarea').val();

  var request = {
    "pipeline": pipeline,
    "dataset": dataset,
    "split": split,
    "table_idx": table_idx,
    "cells": cells,
    "edited_cells": JSON.stringify(editedCells),
    "custom_input": custom_input
  };

  $.ajax({
    type: "POST",
    contentType: "application/json; charset=utf-8",
    url: `${url_prefix}/pipeline`,
    data: JSON.stringify(request),
    success: function (data) {
      output = data["out"];
      set_output(pipeline, output);
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

function init_cell_interactivity() {
  ["th", "td"].forEach(
    function (celltype) {
      var cells = $("#tablearea").find(celltype);
      cells.off("click");
      cells.removeAttr("contenteditable");

      if (mode == "highlight") {
        cells.removeClass("editable-cell");
        cells.addClass("highlightable-cell");
        cells.on("click",
          function () {
            $(this).toggleClass("table-active");
          }
        );
      } else if (mode == "edit") {
        cells.removeClass("highlightable-cell");
        cells.addClass("editable-cell");
        $(".editable-cell").attr("contenteditable", '');
        $(".editable-cell").on("input", function (e) {
          cell_id = $(this).attr("cell-idx");
          content = $(this).text();
          editedCells[cell_id] = content;
          $(this).css("font-style", "italic");
        });
      }
    }
  );
}

function change_dataset() {
  $("#dataset-spinner").show();
  dataset = $('#dataset-select').val();
  table_idx = 0;
  fetch_table(dataset, split, table_idx);
  $("#page-input").val(table_idx);
}

function change_split() {
  $("#dataset-spinner").show();
  split = $('#split-select').val();
  table_idx = 0;
  fetch_table(dataset, split, table_idx);
  $("#page-input").val(table_idx);
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
  var export_option = $('input[name="options-export"]:checked').val();
  if (export_option == "favourites") {
    var filename = "export.zip";
    var export_examples = JSON.stringify(favourites);
  } else {
    var dataset = $('#dataset-select').val();
    var split = $('#split-select').val();
    var filename = `${dataset}_${split}_tab_${table_idx}.${format}`;
    var export_examples = JSON.stringify([{
      "dataset": dataset,
      "split": split,
      "table_idx": table_idx
    }]);
  }
  var request = {
    "export_format": format,
    "export_option": export_option,
    "export_examples": export_examples,
    "edited_cells": JSON.stringify(editedCells)
  };

  postRequestDownload("export_to_file", request, filename);

  $("#exp-btn").html("Export");
  $("#exp-btn").removeClass('disabled');
}

function insert_text(input_text) {
  var textarea = $("#model-api-textarea");
  textarea.val(textarea.val() + input_text);
}

function update_favourite_button() {
  if (`${dataset}-${split}-${table_idx}` in favourites) {
    $("#favourite-btn").css("background-color", "#ffc107");
    // $("#favourite-btn").css("color", "white");
  } else {
    $("#favourite-btn").css("background-color", "");
    // $("#favourite-btn").css("color", "grey");
  }
}

function toggle_edit() {
  if (mode == "edit") {
    $("#edit-btn").css("background-color", "");
    $("#edit-btn").css("color", "");
    mode = "highlight";
  } else {
    $("#edit-btn").css("background-color", "#0175ac");
    $("#edit-btn").css("color", "white");
    mode = "edit";
  }

  init_cell_interactivity();
}

function fetch_table(dataset, split, table_idx, export_format) {
  $.get(`${url_prefix}/table`, {
    "dataset": dataset,
    "table_idx": table_idx,
    "split": split,
    "pipelines": JSON.stringify(pipelines)
  }, function (data) {
    reset_pipeline_outputs();
    reset_edited_cells();
    $("#tablearea").html(data.html);
    $("#dataset-spinner").hide();
    $("#model-api-textarea").val(data.prompt);

    total_examples = data.total_examples;
    $("#total-examples").html(total_examples - 1);
    info = set_dataset_info(data.dataset_info);

    init_cell_interactivity();
    update_favourite_button();

    // for (var pipeline_out of data.pipeline_outputs) {
    //   set_output(pipeline_out["pipeline_name"], pipeline_out["out"]);
    // }
    for (var generated_out of data.generated_outputs) {
      set_output(generated_out["name"], generated_out["out"]);
    }
    for (var pipeline in pipelines) {
      if (pipelines[pipeline].active && $(`#out-${pipeline}-placeholder`).text() == "") {
        run_pipeline(pipeline);
      }
    }
  });
}

// toggling pipelines / outputs
$('.output-checkbox').on('change', function () {
  output_id = $(this)[0].id;
  var output_name = $(`label[for='${output_id}']`).text();

  if ($(this).hasClass("pipeline-checkbox")) {
    // is a pipeline output
    state = pipelines[output_name].active;

    if (state == 1) {
      pipelines[output_name].active = 0;
    } else {
      run_pipeline(output_name);
      pipelines[output_name].active = 1;
    }
  } else {
    state = generated_outputs[output_name].active;
    if (state == 1) {
      // $(`#out-${output_name}`).hide();
      generated_outputs[output_name].active = 0;
    } else {
      // $(`#out-${output_name}`).show();
      generated_outputs[output_name].active = 1;
    }
  }
});

// showing / hiding table
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

// showing / hiding panel
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

$("#dataset-select").on("change", change_dataset);

$("#split-select").on("change", change_split);

$("#format-select").on("change", function (e) {
  $("#dataset-spinner").show();
  fetch_table(dataset, split, table_idx);
});

$(document).keydown(function (event) {
  const key = event.key;

  if (mode == "edit") {
    return;
  }
  if (key === "ArrowRight") {
    event.preventDefault();
    nextbtn();
  } else if (key === "ArrowLeft") {
    event.preventDefault();
    prevbtn();
  }
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

  // enable tooltips
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
  const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
});


