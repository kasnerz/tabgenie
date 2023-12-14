// var url_prefix = window.location.href.split(/[?#]/)[0];
var url_prefix = "";
var table_idx = 0;
var total_examples = 1;
var dataset = window.default_dataset;
var generated_outputs = window.generated_outputs;
var split = "dev";
var select_mode = "select";
var interactive_mode = false;
var view_state = "all";
var mode = window.mode;
var examples_cached = {};
var sizes = mode == "annotate" ? [50, 50] : [70, 30];

if (mode == "annotate") {
  var annotation_set = window.annotation_set;
  total_examples = annotation_set.length;
}

function update_svg_width() {
  if (typeof svg != "undefined") {
    w = $("#svg-body").width();
    svg.attr("width", w);
  }
}

// the draggable divider between the main area and the right panel
var splitInstance = Split(['#centerpanel', '#rightpanel'], {
  sizes: sizes, onDragEnd: function () { update_svg_width }, gutterSize: 1
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

function gotoannotation(page) {
  $(".page-link").removeClass("bg-active");
  $(`#page-link-${page}`).addClass("bg-active");
  // table_idx = annotation_set[page].table_idx;
  // table_idx = page;
  show_annotation();
}

function gotoview(page) {
  fetch_table(dataset, split, table_idx);
  $("#page-input").val(table_idx);
}

function gotopage(page) {
  table_idx = page;
  table_idx = mod(table_idx, total_examples);

  if (mode == "annotate") {
    gotoannotation(page);
  } else {
    gotoview(page);
  }
}


function fetch_annotation(dataset, split, table_idx, annotation_idx) {
  return new Promise((resolve, reject) => {
    // console.log(`fetching ${dataset} ${split} ${table_idx}`);
    $.get(`${url_prefix}/table`, {
      "dataset": dataset,
      "table_idx": table_idx,
      "split": split,
    }, function (data) {
      $('<div>', {
        id: `out-text-${annotation_idx}`,
        class: `annotate-box `,
        style: 'display: none;'
      }).appendTo('#outputarea');
      examples_cached[annotation_idx] = data;

      resolve();
    }).fail(function () {
      reject();
    });
  });
}

function load_annotations() {
  $("#dataset-spinner").show();

  const promises = [];

  for (const [annotation_idx, example] of Object.entries(annotation_set)) {
    const dataset = example.dataset;
    const split = example.split;
    const table_idx = example.table_idx;
    const promise = fetch_annotation(dataset, split, table_idx, annotation_idx);
    promises.push(promise);
  }
  Promise.all(promises)
    .then(() => {
      YPet.addInitializer(function (options) {
        /* Configure the # and colors of Annotation types (minimum 1 required) */
        YPet.AnnotationTypes = new AnnotationTypeList([
          { name: 'Incorrect', color: '#FFBCBC' },
          { name: 'Not checkable', color: '#e9d2ff' },
          { name: 'Misleading', color: '#FFF79F' },
          { name: 'Irrelevant', color: '#ffd99f' },
          { name: 'Other', color: '#bbbbbb' }
        ]);
        var regions = {};
        var paragraphs = {};

        for (const [annotation_idx, data] of Object.entries(examples_cached)) {
          const task = annotation_set[annotation_idx].task;
          const model = annotation_set[annotation_idx].model;
          var task_outputs = data.generated_outputs[task];
          var content = task_outputs.find(o => o.model === model).generated.out;

          var p = new Paragraph({ 'text': content });

          paragraphs[`p${annotation_idx}`] = p;
          regions[`p${annotation_idx}`] = `#out-text-${annotation_idx}`;

          const li = $('<li>', { class: "page-item" });
          const a = $('<a>', { class: "page-link bg-incomplete", style: "min-height: 28px;", id: `page-link-${annotation_idx}` }).text(annotation_idx);
          li.append(a);
          $("#nav-example-cnt").append(li);

          // switch to the corresponding example when clicking on the page number
          $(`#page-link-${annotation_idx}`).click(function () {
            gotopage(annotation_idx);
          });
        }
        YPet.addRegions(regions);

        for (const [p, p_obj] of Object.entries(paragraphs)) {
          YPet[p].show(new WordCollectionView({ collection: p_obj.get('words') }));

          YPet[p].currentView.collection.parentDocument.get('annotations').on('change', function (model,) {
            // var collection = this.parentDocument.get('annotations').toJSON();
            // annotation_set[table_idx]["annotations"] = collection;
          });
          YPet[p].currentView.collection.parentDocument.get('annotations').on('remove', function (model, collection) {
            if (collection.length == 0) {
              collection = [];
            }
            // annotations[table_idx] = collection;
            // console.log(annotations);
          });
          gotoannotation(table_idx);
        }
      });
      YPet.start();

    })
    .catch(() => {
      // Handle errors if any request fails
      console.error("One or more requests failed.");
    })
    .finally(() => {
      // This block will be executed regardless of success or failure
      $("#dataset-spinner").hide();
    });
}

function submit_annotations() {
  console.log(annotation_set);
  $.post({
    url: `${url_prefix}/submit_annotations`,
    contentType: 'application/json', // Specify JSON content type
    data: JSON.stringify(annotation_set),
    success: function (data) {
      $("#overlay-end").show();
    }
  });
}


function mark_annotation_as_complete() {
  $('#page-link-' + table_idx).removeClass("bg-incomplete");
  $('#page-link-' + table_idx).addClass("bg-complete");


  var collection = YPet[`p${table_idx}`].currentView.collection.parentDocument.get('annotations').toJSON();
  annotation_set[table_idx]["annotations"] = collection;
  console.log(annotation_set[table_idx]);

  // if all the examples are annotated, post the annotations
  if ($(".bg-incomplete").length == 0) {
    // show the `submit` button
    $("#submit-annotations-btn").show();

  } else if (table_idx < total_examples - 1) {
    nextbtn();
  }
}

function show_annotation() {
  $(".annotate-box").hide();
  $(`#out-text-${table_idx}`).show();

  data = examples_cached[table_idx];

  $("#tablearea").html(data.html);
  // use <pre> to preserve whitespace
  const rawDataStr = JSON.stringify(data.raw_data, null, 2);
  $("#rawarea").html(`<pre>${rawDataStr}</pre>`);

  const dataset = annotation_set[table_idx].dataset;
  let textType;
  // ["openweather", "basketball", "gsmarena", "wikidata", "owid"]
  if (dataset == "openweather") {
    textType = "Weather forecast";
  } else if (dataset == "basketball") {
    textType = "Basketball game summary";
  } else if (dataset == "gsmarena") {
    textType = "Product description";
  } else if (dataset == "wikidata") {
    textType = "Graph description";
  } else if (dataset == "owid") {
    textType = "Chart caption";
  }
  $("#text-type").html(`<b>${textType}</b>`);

}


function permalinkbtn() {
  let permalink = `${url_prefix}?dataset=${dataset}&split=${split}&table_idx=${table_idx}`;

  popover = bootstrap.Popover.getOrCreateInstance("#permalink-btn");
  popover.setContent({
    '.popover-body': permalink
  });
  $('#permalink-btn').popover('show');
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


function toggle_raw() {
  // toggle display: none on rawarea and tablearea
  $("#rawarea").toggle();
  $("#tablearea").toggle();
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


function set_output(name, output) {
  var placeholder = $(`#out-${name}-placeholder`);
  placeholder.html(output);
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
  // var pressed_props = get_pressed_props();
  $.get(`${url_prefix}/table`, {
    "dataset": dataset,
    "table_idx": table_idx,
    "split": split,
  }, function (data) {
    // reset_edited_cells();
    $("#tablearea").html(data.html);
    // use <pre> to preserve whitespace
    const rawDataStr = JSON.stringify(data.raw_data, null, 2);
    $("#rawarea").html(`<pre>${rawDataStr}</pre>`);
    $("#dataset-spinner").hide();

    total_examples = data.total_examples;

    $("#total-examples").html(total_examples - 1);
    show_generated_outputs(data.generated_outputs);
  });
}


$("#dataset-select").on("change", change_dataset);
$("#split-select").on("change", change_split);


// $("#format-select").on("change", function (e) {
//   $("#dataset-spinner").show();
//   fetch_table(dataset, split, table_idx);
// });

// $('#export-format-select').on("change", function () {
//   // $('#checkbox-table-props').prop('disabled', this.value == 'csv');

//   if (this.value == 'txt') {
//     $('#linearization-format-block').css('display', 'inline-block');
//   } else {
//     $('#linearization-format-block').css('display', 'none');
//   }
// })

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

$("#hideOverlayBtn").click(function () {
  $("#overlay-start").fadeOut();
});

$(document).ready(function () {
  if (mode == "annotate") {
    load_annotations();

    $("#total-examples").html(total_examples - 1);
  } else {
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
  }

  // enable tooltips
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
  const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
});
