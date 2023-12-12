var url_prefix = window.location.href.split(/[?#]/)[0];
// var url_prefix = "";
var table_idx = 0;
var total_examples = 1;
var dataset = window.default_dataset;
var pipelines = window.pipelines;
var prompts = window.prompts;
var generated_outputs = window.generated_outputs;
var favourites = window.favourites;
var editedCells = window.editedCells; // TODO check updated all places
var split = "dev";
var select_mode = "select";
var interactive_mode = false;
var view_state = "all";

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

function get_note_id(dataset, split, table_idx) {
  return `${dataset}-${split}-${table_idx}`;
}

function get_favourite_id(dataset, split, table_idx) {
  return `${dataset}-${split}-${table_idx}`;
}

function favouritebtn() {
  let favourite_id = get_favourite_id(dataset, split, table_idx);
  if (favourite_id in favourites) {
    remove_favourite(dataset, split, table_idx);
  } else {
    insert_favourite(dataset, split, table_idx)
  }
}


function permalinkbtn() {
  let permalink = `${url_prefix}?dataset=${dataset}&split=${split}&table_idx=${table_idx}`;

  popover = bootstrap.Popover.getOrCreateInstance("#permalink-btn");
  popover.setContent({
    '.popover-body': permalink
  });
  $('#permalink-btn').popover('show');
}

function insert_favourite(dataset, split, table_idx) {
  let favourite_id = get_favourite_id(dataset, split, table_idx)

  function local_insert_favourite() {
    favourites[favourite_id] = { "dataset": dataset, "split": split, "table_idx": table_idx };

    update_favourite_button(favourite_id);

    $("#favourites-area").attr("hidden", false);
    $("#btn-export-favourites").removeAttr("disabled");
    $("#btn-export-favourites").addClass("btn-primary").removeClass("btn-secondary");

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
      .addClass("favourite-item")
      .attr("id", `fav-${favourite_id}`);

    li_el.append(span_el);

    $("#favourites-box").append(li_el);
  }

  var request = {
    "action": "insert",
    "dataset": dataset,
    "split": split,
    "table_idx": table_idx,
  };
  $.ajax({
    type: "POST",
    contentType: "application/json; charset=utf-8",
    url: `${url_prefix}/favourite`,
    data: JSON.stringify(request),
    success: function (server_favourites) {
      favourites = server_favourites
      local_insert_favourite();
    },
    error: function (xhr, error) {
      msg = `Failed to store action to server: Insert favourite ${favourite_id}`;
      alert(msg)
      local_insert_favourite();  // still apply the action at least locally
    },
    dataType: "json",
  });
}


function remove_favourite(dataset, split, table_idx) {
  let favourite_id = get_favourite_id(dataset, split, table_idx)

  function local_remove_favourite() {
    delete favourites[favourite_id];
    $(`#fav-${favourite_id}`).remove();
    update_favourite_button(favourite_id);

    if ($.isEmptyObject(favourites)) {
      // $("#favourites-area").attr("hidden", true);
      $("#btn-export-favourites").attr("disabled", true);
      $("#btn-export-favourites").addClass("btn-secondary").removeClass("btn-primary");
    }
  }

  var request = {
    "action": "remove",
    "dataset": dataset,
    "split": split,
    "table_idx": table_idx,
  };
  $.ajax({
    type: "POST",
    contentType: "application/json; charset=utf-8",
    url: `${url_prefix}/favourite`,
    data: JSON.stringify(request),
    success: function (server_favourites) {
      favourites = server_favourites
      local_remove_favourite();
    },
    error: function (xhr, error) {
      msg = `Failed to store action to server: Removed favourite ${favourite_id}`
      console.log(msg)
      alert(msg)
      local_remove_favourite();  // still apply the action at least locally
    },
    dataType: "json",
  });
}

function clear_favourites() {
  function local_clear_favourites() {
    favourites = {};
    $(".favourite-item").remove();
    update_favourite_button(get_favourite_id(dataset, split, table_idx));
  }
  $.ajax({
    type: "POST",
    contentType: "application/json; charset=utf-8",
    url: `${url_prefix}/favourite`,
    data: JSON.stringify({ "action": "remove_all" }),
    success: function (server_favourites) {
      if (Object.keys(server_favourites).length != 0) {
        console.log(`WARNING successful remove_all to favourite did not remove all: ${server_favourites}`)
      }
      local_clear_favourites();
    },
    error: function (xhr, error) {
      local_clear_favourites();
      msg = "Failed to store action to server: Removed ALL favourites";
      console.log(msg);
      alert(msg);
    },
    dataType: "json",
  });
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

function get_pressed_props() {
  var pressed_props = [];
  $(".prop-btn[aria-expanded='true']").each(function () {
    pressed_props.push($(this).text());
  });
  return pressed_props;
}

function toggle_props() {
  // first show all, if all is shown then hide all
  if ($(".prop-btn[aria-expanded='false']").length != 0) {
    $(".prop-btn[aria-expanded='false']").click();
  } else {
    $(".prop-btn").click();
  }
}

function toggle_view() {
  if (view_state == "all") { // all -> table
    splitInstance.collapse(1);
    $('.gutter').hide();
    view_state = "table";
  } else if (view_state == "table") { // table -> out
    splitInstance.collapse(0);
    view_state = "out";
  } else if (view_state == "out") { // out -> all
    splitInstance.setSizes([70, 30])
    $('.gutter').show();
    view_state = "all";
  }
  update_svg_width();
}

function toggle_raw() {
  // toggle display: none on rawarea and tablearea
  $("#rawarea").toggle();
  $("#tablearea").toggle();
}


function clear_notes() {
  function local_clear_notes() {
    notes = {};
    update_note_pen_background(get_note_id(dataset, split, table_idx));
    update_notes_modal();
  }
  $.ajax({
    type: "POST",
    contentType: "application/json; charset=utf-8",
    url: `${url_prefix}/note`,
    data: JSON.stringify({ "action": "remove_all" }),
    success: function (server_notes) {
      if (Object.keys(server_notes).length != 0) {
        console.log(`WARNING successful remove_all to notes did not remove all: ${server_notes}`)
      }
      local_clear_notes();
    },
    error: function (xhr, error) {
      local_clear_notes();
      msg = "Failed to store action to server: Removed ALL notes";
      console.log(msg);
      alert(msg);
    },
    dataType: "json",
  });
}

function set_note(dataset, split, table_idx) {
  let note_id = get_note_id(dataset, split, table_idx);
  if (note_id in notes) {
    msg = notes[note_id]["note"];
    $(".modalNoteInput").val(msg);
  } else {
    $(".modalNoteInput").val("");
  }
  update_note_pen_background(note_id);
}

function update_note_pen_background(note_id) {
  if (note_id in notes) {
    $("#note-btn").css("background-color", "#FFF68F");
  } else {
    $("#note-btn").css("background-color", "");
  }
}

function update_notes_modal() {
  if ($.isEmptyObject(notes)) {
    $("#notes-area").attr("hidden", true);

    $("#btn-export-notes").attr("disabled", true);
    $("#btn-export-notes").addClass("btn-secondary").removeClass("btn-primary");

  } else {
    $("#notes-area").attr("hidden", false);

    $("#btn-export-notes").removeAttr("disabled");
    $("#btn-export-notes").addClass("btn-primary").removeClass("btn-secondary");
  }

  $("#notes-box").html("");
  for (const [note_id, note_d] of Object.entries(notes)) {

    console.log(notes);

    var btn_remove = $("<button></button>")
      .attr("type", "button")
      .css("width", "0.5em !important")
      .addClass("btn")
      .attr("onclick", `save_note_val('${note_id}', '');`)
      .text("✕");

    let ndataset = note_d["dataset"];
    let nsplit = note_d["split"];
    let ntable_idx = note_d["table_idx"];

    let ncontent = note_d["note"];

    var span_el = $("<span></span>")
      .addClass("clickable")
      .text(`${note_id}`)
      .attr("onclick", `gotoexample('${ndataset}', '${nsplit}', '${ntable_idx}');`);

    // show first 100 characters of the note content next to the clickable button
    if (ncontent.length > 100) {
      ncontent = ncontent.substring(0, 100) + "...";
    }
    var content_el = $("<span></span>").text(` [${ncontent}]`).css("font-style", "italic");

    var li_el = $("<li></li>")
      .addClass("list-group-item")
      .addClass("note-item")
      .attr("id", `note-${note_id}`);

    li_el.append(span_el);
    li_el.append(content_el);
    li_el.append(btn_remove);

    $("#notes-box").append(li_el);
  }
}

function save_note() {
  let note = $(".modalNoteInput").val();
  let note_id = get_note_id(dataset, split, table_idx);
  save_note_val(note_id, note);
  $("#checkbox-notes").removeAttr("disabled");
}

function delete_note() {
  $(".modalNoteInput").val("");
  let note_id = get_note_id(dataset, split, table_idx);
  save_note_val(note_id, "");
}

function save_note_val(note_id, note) {
  var request = {
    "action": "edit_note",
    "dataset": dataset,
    "split": split,
    "table_idx": table_idx,
    "note": note,
  };
  function after_save_note_val() {
    update_note_pen_background(note_id);
    update_notes_modal();
  }
  $.ajax({
    type: "POST",
    contentType: "application/json; charset=utf-8",
    url: `${url_prefix}/note`,
    data: JSON.stringify(request),
    success: function (server_notes) {
      notes = server_notes;
      after_save_note_val();
    },
    error: function (xhr, error) {
      msg = `Failed to store action to server: save_note ${note_id}`;
      alert(msg)
      // still apply the action at least locally
      if (note.length > 0) {
        notes[note_id] = note;
      }
      after_save_note_val();
    },
    dataType: "json",
  });
}

function set_dataset_info(info) {
  var ex_array = $.map(info.examples, function (num, split) {
    return $("<li/>").append([$("<b/>").text(`${split}: `), $("<span/>").text(num)]);
  });
  var links_array = $.map(info.links, function (url, page) {
    return $("<li/>").append([$("<b/>").text(`${page}: `), $("<a/>", { href: url, text: url })]);
  });

  $("#dataset-info").empty();
  $("#dataset-info").append([
    $("<h3/>").text(info.name),
    $("<p/>").text(info.description),
    $("<h5/>").text("Number of examples"),
    $("<p/>").append(
      $("<ul/>").append(ex_array)),
    $("<h5/>").text("Links"),
    $("<p/>").append(
      $("<ul/>").append(links_array)),
    $("<h5/>").text("Version"),
    $("<p/>").text(info.version),
    $("<h5/>").text("Changes in our version"),
    $("<p/>").text(info.changes),
    $("<h5/>").text("License"),
    $("<p/>").text(info.license),
    $("<h5/>").text("Citation"),
    $("<p/>").append($("<code/>").html(info.citation.replace(/\n/g, '<br>'))),
  ]
  );
}

function get_highlighted_cells() {
  var activeCells = $("#tablearea").find(".table-active").map(
    function () {
      return $(this).attr("cell-idx");
    }).get();

  // // no highlighted cells -> send all cells except headers
  // if (activeCells.length == 0) {
  //   activeCells = $("#tablearea").find("td").map(
  //     function () {
  //       return $(this).attr("cell-idx");
  //     }).get();
  // }

  return activeCells;
}

function set_output(name, output) {
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
  $("#checkbox-edited-cells").attr("disabled", true);
}

function run_pipeline(pipeline) {
  var cells = get_highlighted_cells();
  var dataset = $('#dataset-select').val();
  var split = $('#split-select').val();
  var custom_inputs = $(`.${pipeline}-input`).val();

  var request = {
    "pipeline": pipeline,
    "dataset": dataset,
    "split": split,
    "table_idx": table_idx,
    "edited_cells": JSON.stringify(editedCells),
    "custom_input": custom_inputs
  };
  if (cells.length > 0) {
    request["cells"] = cells;
  }
  $(`#pipeline-${pipeline}-spinner`).show();

  $.ajax({
    type: "POST",
    contentType: "application/json; charset=utf-8",
    url: `${url_prefix}/pipeline`,
    data: JSON.stringify(request),
    success: function (data) {
      output = data["out"];
      $(`#pipeline-${pipeline}-spinner`).hide();
      set_output(pipeline, output);
    },
    dataType: "json"
  });
}

function reload_pipeline(pipeline) {
  set_output(pipeline, "");
  run_pipeline(pipeline);
}

function update_cell_interactivity() {
  ["th", "td"].forEach(
    function (celltype) {
      var cells = $("#main-table-body").find(celltype);
      cells.off("click");
      cells.removeAttr("contenteditable");

      if (select_mode == "select") {
        cells.removeClass("editable-cell");
        cells.removeClass("highlightable-cell");
      }
      else if (select_mode == "highlight") {
        cells.removeClass("editable-cell");
        cells.addClass("highlightable-cell");
        cells.on("click",
          function () {
            $(this).toggleClass("table-active");
          }
        );
      } else if (select_mode == "edit") {
        cells.removeClass("highlightable-cell");
        cells.addClass("editable-cell");
        $(".editable-cell").attr("contenteditable", '');
        $(".editable-cell").on("input", function (e) {
          cell_id = $(this).attr("cell-idx");
          content = $(this).text();
          editedCells[cell_id] = content;
          $(this).css("font-style", "italic");
          $("#checkbox-edited-cells").removeAttr("disabled");
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

function change_mode() {
  select_mode = $("input:radio[name ='interactive-mode-radio']:checked").val();
  update_cell_interactivity();
}

function change_task() {
  const task = $("input:radio[name ='task-toggle-radio']:checked").val();
  // unhide box-${task} and hide others
  $(".generated-output-box").hide();
  $(".box-" + task).show();
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


function export_table(export_option) {
  var format = $('#export-format-select').val();
  var linearization_style = $('#linearization-format-select').val();
  var include_props = $('#checkbox-table-props').is(":checked");
  var export_edited_cells = $('#checkbox-edited-cells').is(":checked");
  var export_notes = $('#checkbox-notes').is(":checked");

  if (export_option == "favourites") {
    var filename = "tabgenie_favourites.zip";
    // TODO fetch favourites using AJAX
    // just notify user that exporting local copy of failure on fetch favourites failure
    var export_examples = JSON.stringify(favourites);
  } else if (export_option == "notes") {
    var filename = "tabgenie_notes.zip";
    var export_examples = JSON.stringify(notes);
  } else {
    var dataset = $('#dataset-select').val();
    var split = $('#split-select').val();
    var filename = `tabgenie_${dataset}_${split}_tab_${table_idx}.${format}`;
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
    "linearization_style": linearization_style,
    "include_props": include_props,
    "export_notes": export_notes
  };

  if (export_edited_cells) {
    request["edited_cells"] = JSON.stringify(editedCells);
  }

  postRequestDownload("export_to_file", request, filename);
}

function insert_prompt(prompt_name, id) {
  var textarea = $(`#${id}`);
  textarea.val(prompts[prompt_name]);
  textarea.highlightWithinTextarea("update");
}

function update_favourite_button(favourite_id) {
  if (favourite_id in favourites) {
    $("#favourite-btn").css("background-color", "#FFF68F");
  } else {
    $("#favourite-btn").css("background-color", "");
  }
}

function toggle_interactive() {
  interactive_mode = !interactive_mode;
  $("#mode-selectarea").toggle();
  $("#pipelinearea").toggle();
  update_cell_interactivity();
  refresh_pipelines();
}

function refresh_pipelines() {
  if (!interactive_mode) {
    return;
  }
  for (var pipeline in pipelines) {
    if ( // pipeline should not be active for the dataset
      (("datasets" in pipelines[pipeline]) && !(pipelines[pipeline]["datasets"].includes(dataset)))
      // pipeline is not interactive
      || !pipelines[pipeline].interactive
    ) {
      $(`#out-${pipeline}`).hide();
      pipelines[pipeline].active = 0;
    } else {
      // activate the pipeline
      $(`#out-${pipeline}`).show();
      // $(`#pipeline-checkbox-${pipeline}`).prop("checked", true);
      pipelines[pipeline].active = 1;
    }
    // run the active pipelines
    if (pipelines[pipeline].active && $(`#out-${pipeline}-placeholder`).text() == "") {
      run_pipeline(pipeline);
    }
  }
}

function show_generated_outputs(generated_outputs) {
  $(".generated-output-box").remove();

  for (const [task, task_outputs] of Object.entries(generated_outputs)) {
    // sort task_outputs by model name
    task_outputs.sort(function (a, b) {
      return a.model.localeCompare(b.model);
    });
    for (out_obj of task_outputs) {
      const name = out_obj.model;
      var placeholder = $('<div>', { id: `out-${name}-placeholder`, class: "font-mono" });
      var label = $('<label>', { class: "label-name" }).text(name);
      if (!out_obj.generated) {
        continue;
      }
      var content = out_obj.generated.out;
      placeholder.html(content);
      $('<div>', {
        id: `out-${name}`,
        class: `output-box generated-output-box box-${task}`,
        style: 'display: none;'
      }).append(label).append(placeholder).appendTo('#outputarea');
    }
  }
  $("input:radio[name ='task-toggle-radio']").on("change", change_task);
  // set the first task as active
  $("input:radio[name ='task-toggle-radio']").first().prop("checked", true);
  change_task();
}

function fetch_table(dataset, split, table_idx) {
  var pressed_props = get_pressed_props();
  $.get(`${url_prefix}/table`, {
    "dataset": dataset,
    "table_idx": table_idx,
    "split": split,
    "displayed_props": JSON.stringify(pressed_props),
    // "pipelines": JSON.stringify(pipelines)
  }, function (data) {

    reset_pipeline_outputs();
    reset_edited_cells();
    $("#tablearea").html(data.html);
    // use <pre> to preserve whitespace
    const rawDataStr = JSON.stringify(data.raw_data, null, 2);
    $("#rawarea").html(`<pre>${rawDataStr}</pre>`);
    $("#dataset-spinner").hide();

    total_examples = data.total_examples;

    $("#total-examples").html(total_examples - 1);


    update_cell_interactivity();
    // set_dataset_info(data.dataset_info);

    // console.log(`favourites before update ${JSON.stringify(favourites)}`)
    // console.log(`received session ${JSON.stringify(data.session)}`)
    // favourites = data.session.favourites;
    // update_favourite_button(get_favourite_id(dataset, split, table_idx));
    // notes = data.session.notes;
    // set_note(dataset, split, table_idx);
    // update_notes_modal();

    // console.log(data.generated_outputs);
    show_generated_outputs(data.generated_outputs);
    refresh_pipelines();
  });
}

// toggling pipelines
$('.output-checkbox').on('change', function () {
  output_id = $(this)[0].id;
  var output_name = $(`label[for='${output_id}']`).text();
  state = pipelines[output_name].active;

  if (state == 1) {
    pipelines[output_name].active = 0;
    set_output(output_name, "");
  } else {
    run_pipeline(output_name);
    pipelines[output_name].active = 1;
  }
});



$("#dataset-select").on("change", change_dataset);

$("#split-select").on("change", change_split);

$("input:radio[name ='interactive-mode-radio']").on("change", change_mode);

$("#format-select").on("change", function (e) {
  $("#dataset-spinner").show();
  fetch_table(dataset, split, table_idx);
});

$('#export-format-select').on("change", function () {
  $('#checkbox-table-props').prop('disabled', this.value == 'csv');

  if (this.value == 'txt') {
    $('#linearization-format-block').css('display', 'inline-block');
  } else {
    $('#linearization-format-block').css('display', 'none');
  }
})

$(".custom-prompt-input").highlightWithinTextarea({
  highlight: [
    {
      // highlight: /\[PROMPTVAR:[a-z0-9_]*\]/gi,
      highlight: "[PROMPTVAR:TASK_DEF]",
      className: 'yellow'
    },
    {
      highlight: /\[PROMPTVAR:[a-z0-9_]*\]/gi,
      className: 'blue'
    }
  ]
});

$(document).keydown(function (event) {
  const key = event.key;

  if (select_mode == "edit") {
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
  if (window.display_table != null) {
    gotoexample(window.display_table.dataset, window.display_table.split, window.display_table.table_idx);
    // wait until the request is returned and total_examples is set, then go to table
    setInterval(function () {
      if (total_examples > 1) {
        gotopage(window.display_table.table_idx);
        clearInterval(this);
      }
    }, 1000);
  }
  else {
    // load default dataset
    $("#dataset-select").val(dataset).change();
    $("#page-input").val(table_idx);
  }

  // enable tooltips
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
  const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
});

function Meteogram(json, container) {
  // Parallel arrays for the chart data, these are populated as the JSON file
  // is loaded
  this.symbols = [];
  this.precipitations = [];
  this.precipitationsError = []; // Only for some data sets
  this.winds = [];
  this.temperatures = [];
  this.pressures = [];

  this.json = json;
  this.container = container;

  this.parseData();
}

/**
* Draw the weather symbols on top of the temperature series. The symbols are
* fetched from yr.no's MIT licensed weather symbol collection.
* https://github.com/YR/weather-symbols
*/
Meteogram.prototype.drawWeatherSymbols = function (chart) {

  chart.series[0].data.forEach((point, i) => {
    if (this.resolution > 36e5 || i % 2 === 0) {
      const symbol = this.symbols[i];

      const noDayOrNight = ["04", "09", "10", "11", "12", "13", "14", "15", "22", "23", "30", "31", "32", "33", "34", "46", "47", "48", "49", "50"];

      // if first two characters of symbol in noDayOrNight, stripe of "d" or "n"
      const symbolDayOrNight = noDayOrNight.includes(symbol.substring(0, 2)) ? symbol.substring(0, 2) : symbol;

      chart.renderer
        .image(
          'https://cdn.jsdelivr.net/gh/nrkno/yr-weather-symbols' +
          `@8.0.1/dist/svg/${symbolDayOrNight}.svg`,
          point.plotX + chart.plotLeft - 8,
          point.plotY + chart.plotTop - 30,
          30,
          30
        )
        .attr({
          zIndex: 5
        })
        .add();
    }
  });
};


/**
* Draw blocks around wind arrows, below the plot area
*/
Meteogram.prototype.drawBlocksForWindArrows = function (chart) {
  const xAxis = chart.xAxis[0];

  for (
    let pos = xAxis.min, max = xAxis.max, i = 0;
    pos <= max + 36e5; pos += 36e5,
    i += 1
  ) {

    // Get the X position
    const isLast = pos === max + 36e5,
      x = Math.round(xAxis.toPixels(pos)) + (isLast ? 0.5 : -0.5);

    // Draw the vertical dividers and ticks
    const isLong = this.resolution > 36e5 ?
      pos % this.resolution === 0 :
      i % 2 === 0;

    chart.renderer
      .path([
        'M', x, chart.plotTop + chart.plotHeight + (isLong ? 0 : 28),
        'L', x, chart.plotTop + chart.plotHeight + 32,
        'Z'
      ])
      .attr({
        stroke: chart.options.chart.plotBorderColor,
        'stroke-width': 1
      })
      .add();
  }

  // Center items in block
  chart.get('windbarbs').markerGroup.attr({
    translateX: chart.get('windbarbs').markerGroup.translateX + 8
  });

};

/**
* Build and return the Highcharts options structure
*/
Meteogram.prototype.getChartOptions = function (cityName) {
  return {
    chart: {
      renderTo: this.container,
      marginBottom: 70,
      marginRight: 40,
      marginTop: 50,
      plotBorderWidth: 1,
      height: 310,
      alignTicks: false,
      scrollablePlotArea: {
        minWidth: 720
      },
      animation: false
    },

    defs: {
      patterns: [{
        id: 'precipitation-error',
        path: {
          d: [
            'M', 3.3, 0, 'L', -6.7, 10,
            'M', 6.7, 0, 'L', -3.3, 10,
            'M', 10, 0, 'L', 0, 10,
            'M', 13.3, 0, 'L', 3.3, 10,
            'M', 16.7, 0, 'L', 6.7, 10
          ].join(' '),
          stroke: '#68CFE8',
          strokeWidth: 1
        }
      }]
    },

    title: {
      text: cityName,
      align: 'left',
      style: {
        whiteSpace: 'nowrap',
        textOverflow: 'ellipsis'
      }
    },


    tooltip: {
      shared: true,
      useHTML: true,
      headerFormat:
        '<small>{point.x:%A, %b %e, %H:%M} - {point.point.to:%H:%M}</small><br>' +
        '<b>{point.point.symbolName}</b><br>'

    },

    xAxis: [{ // Bottom X axis
      type: 'datetime',
      tickInterval: 2 * 36e5, // two hours
      minorTickInterval: 36e5, // one hour
      tickLength: 0,
      gridLineWidth: 1,
      gridLineColor: 'rgba(128, 128, 128, 0.1)',
      startOnTick: false,
      endOnTick: false,
      minPadding: 0,
      maxPadding: 0,
      offset: 30,
      showLastLabel: true,
      labels: {
        format: '{value:%H}'
      },
      crosshair: true
    }, { // Top X axis
      linkedTo: 0,
      type: 'datetime',
      tickInterval: 24 * 3600 * 1000,
      labels: {
        format: '{value:<span style="font-size: 12px; font-weight: bold">%a</span> %b %e}',
        align: 'left',
        x: 3,
        y: 8
      },
      opposite: true,
      tickLength: 20,
      gridLineWidth: 1
    }],

    yAxis: [{ // temperature axis
      title: {
        text: null
      },
      labels: {
        format: '{value}°',
        style: {
          fontSize: '10px'
        },
        x: -3
      },
      plotLines: [{ // zero plane
        value: 0,
        color: '#BBBBBB',
        width: 1,
        zIndex: 2
      }],
      maxPadding: 0.3,
      minRange: 8,
      tickInterval: 1,
      gridLineColor: 'rgba(128, 128, 128, 0.1)'

    }, { // precipitation axis
      title: {
        text: null
      },
      labels: {
        enabled: false
      },
      gridLineWidth: 0,
      tickLength: 0,
      minRange: 10,
      min: 0

    }, { // Air pressure
      allowDecimals: false,
      title: { // Title on top of axis
        text: 'hPa',
        offset: 0,
        align: 'high',
        rotation: 0,
        style: {
          fontSize: '10px',
          color: Highcharts.getOptions().colors[2]
        },
        textAlign: 'left',
        x: 3
      },
      labels: {
        style: {
          fontSize: '8px',
          color: Highcharts.getOptions().colors[2]
        },
        y: 2,
        x: 3
      },
      gridLineWidth: 0,
      opposite: true,
      showLastLabel: false
    }],

    legend: {
      enabled: false
    },

    plotOptions: {
      series: {
        pointPlacement: 'between',
        animation: false
      }
    },


    series: [{
      name: 'Temperature',
      data: this.temperatures,
      type: 'spline',
      marker: {
        enabled: false,
        states: {
          hover: {
            enabled: true
          }
        }
      },
      tooltip: {
        pointFormat: '<span style="color:{point.color}">\u25CF</span> ' +
          '{series.name}: <b>{point.y}°C</b><br/>'
      },
      zIndex: 1,
      color: '#FF3333',
      negativeColor: '#48AFE8'
    }, {
      name: 'Precipitation',
      data: this.precipitationsError,
      type: 'column',
      color: 'url(#precipitation-error)',
      yAxis: 1,
      groupPadding: 0,
      pointPadding: 0,
      tooltip: {
        valueSuffix: ' mm',
        pointFormat: '<span style="color:{point.color}">\u25CF</span> ' +
          '{series.name}: <b>{point.minvalue} mm - {point.maxvalue} mm</b><br/>'
      },
      grouping: false,
      dataLabels: {
        enabled: this.hasPrecipitationError,
        filter: {
          operator: '>',
          property: 'maxValue',
          value: 0
        },
        style: {
          fontSize: '8px',
          color: 'gray'
        }
      }
    }, {
      name: 'Precipitation',
      data: this.precipitations,
      type: 'column',
      color: '#68CFE8',
      yAxis: 1,
      groupPadding: 0,
      pointPadding: 0,
      grouping: false,
      dataLabels: {
        enabled: !this.hasPrecipitationError,
        filter: {
          operator: '>',
          property: 'y',
          value: 0
        },
        style: {
          fontSize: '8px',
          color: '#666'
        }
      },
      tooltip: {
        valueSuffix: ' mm'
      }
    }, {
      name: 'Air pressure',
      color: Highcharts.getOptions().colors[2],
      data: this.pressures,
      marker: {
        enabled: false
      },
      shadow: false,
      tooltip: {
        valueSuffix: ' hPa'
      },
      dashStyle: 'shortdot',
      yAxis: 2
    }, {
      name: 'Wind',
      type: 'windbarb',
      id: 'windbarbs',
      color: Highcharts.getOptions().colors[1],
      lineWidth: 1.5,
      data: this.winds,
      vectorLength: 18,
      yOffset: -15,
      tooltip: {
        valueSuffix: ' m/s'
      }
    }]
  };
};

/**
* Post-process the chart from the callback function, the second argument
* Highcharts.Chart.
*/
Meteogram.prototype.onChartLoad = function (chart) {

  this.drawWeatherSymbols(chart);
  this.drawBlocksForWindArrows(chart);

};

/**
* Create the chart. This function is called async when the data file is loaded
* and parsed.
*/
Meteogram.prototype.createChart = function (cityName) {
  this.chart = new Highcharts.Chart(this.getChartOptions(cityName), chart => {
    this.onChartLoad(chart);
  });
};

Meteogram.prototype.error = function () {
  document.getElementById('loading').innerHTML =
    '<i class="fa fa-frown-o"></i> Failed loading data, please try again later';
};

Meteogram.prototype.parseData = function () {
  let pointStart;

  if (!this.json || !this.json.list) {
    return this.error();
  }

  // Loop over hourly forecasts
  this.json.list.forEach((data, i) => {

    const x = Date.parse(data.dt_txt),
      weather = data.weather[0],
      symbolCode = weather.icon,
      to = x + 3 * 36e5; // Assuming each forecast is 3 hours apart

    // if (to > pointStart + 48 * 36e5) {
    //     return;
    // }

    // Populate the parallel arrays
    this.symbols.push(symbolCode);
    this.temperatures.push({
      x,
      y: data.main.temp,
      // custom options used in the tooltip formatter
      to,
      symbolName: symbolCode
    });

    this.precipitations.push({
      x,
      y: data.rain ? data.rain['3h'] : 0
    });

    if (i % 2 === 0) {
      this.winds.push({
        x,
        value: data.wind.speed,
        direction: data.wind.deg
      });
    }

    this.pressures.push({
      x,
      y: data.main.pressure
    });

    if (i === 0) {
      pointStart = (x + to) / 2;
    }
  });

  const city = this.json.city;
  const cityName = city.name + " (" + city.country + ")";
  // Create the chart when the data is loaded

  this.createChart(cityName);
};
// End of the Meteogram protype


