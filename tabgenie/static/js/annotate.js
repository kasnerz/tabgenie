// var url_prefix = window.location.href.split(/[?#]/)[0];
var url_prefix = "";
var table_idx = 0;


function update_svg_width() {
  if (typeof svg != "undefined") {
    w = $("#svg-body").width();
    svg.attr("width", w);
  }
}

// the draggable divider between the main area and the right panel
var splitInstance = Split(['#centerpanel', '#rightpanel'], {
  sizes: [50, 50], onDragEnd: function () { update_svg_width }, gutterSize: 1
});

function randint(max) {
  return Math.floor(Math.random() * max);
}

function mod(n, m) {
  return ((n % m) + m) % m;
}

function gotopage(page) {
  table_idx = annotation_set[page].table_idx;
  const dataset = annotation_set[page].dataset;
  const split = annotation_set[page].split;

  fetch_table(dataset, split, table_idx);
  $("#page-input").val(table_idx);
}

function nextbtn() {
  gotopage(table_idx + 1);
}

function gotobtn() {
  var n = $("#page-input").val();
  gotopage(n);
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

function set_output(name, output) {
  var placeholder = $(`#out-${name}-placeholder`);
  placeholder.html(output);
}

function toggle_raw() {
  // toggle display: none on rawarea and tablearea
  $("#rawarea").toggle();
  $("#tablearea").toggle();
}



function fetch_table(dataset, split, table_idx) {
  $.get(`${url_prefix}/table`, {
    "dataset": dataset,
    "table_idx": table_idx,
    "split": split,
  }, function (data) {
    $("#tablearea").html(data.html);
    // use <pre> to preserve whitespace
    const rawDataStr = JSON.stringify(data.raw_data, null, 2);
    $("#rawarea").html(`<pre>${rawDataStr}</pre>`);
    $("#dataset-spinner").hide();

    show_annotation(data.generated_outputs);
  });
}

function display_example(table_idx) {
  const dataset = annotation_set[table_idx].dataset;
  const split = annotation_set[table_idx].split;
  fetch_table(dataset, split, table_idx);
}

$(document).keydown(function (event) {
  const key = event.key;

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

  display_example(table_idx);
  $("#page-input").val(table_idx);
  $("#total-examples").html(total_examples - 1);

  // enable tooltips
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
  const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
});
