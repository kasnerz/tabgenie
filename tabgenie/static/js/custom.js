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
var sizes = mode == "annotate" ? [50, 50] : [66, 33];

const error_colors = [
    { name: 'Incorrect', color: '#FFBCBC' },
    { name: 'Not checkable', color: '#e9d2ff' },
    { name: 'Misleading', color: '#FFF79F' },
    { name: 'Other', color: '#bbbbbb' }
]

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
                YPet.AnnotationTypes = new AnnotationTypeList(error_colors);
                var regions = {};
                var paragraphs = {};

                for (const [annotation_idx, data] of Object.entries(examples_cached)) {
                    const setup = annotation_set[annotation_idx].setup;
                    const model = annotation_set[annotation_idx].model;
                    var content = data.generated_outputs.find(o => o.setup.name == setup && o.model == model).generated;

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
    // console.log(annotation_set);
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
    // console.log(annotation_set[table_idx]);

    // if all the examples are annotated, post the annotations
    if ($(".bg-incomplete").length == 0) {
        // show the `submit` button
        $("#submit-annotations-btn").show();

        // scroll to the top
        $('html, body').animate({
            scrollTop: $("#submit-annotations-btn").offset().top
        }, 500);

    } else if (table_idx < total_examples - 1) {
        nextbtn();
    }
}

function show_raw_data(data) {
    // use <pre> to preserve whitespace
    var rawDataStr = JSON.stringify(data.raw_data, null, 2).replace(/\\n/g, '<br>');

    if (rawDataStr[0] == '"') {
        // remove the first and last double quotes
        rawDataStr = rawDataStr.slice(1, -1);
    }

    $("#rawarea").html(`<pre>${rawDataStr}</pre>`);
}

function show_annotation() {
    $(".annotate-box").hide();
    $(`#out-text-${table_idx}`).show();

    data = examples_cached[table_idx];

    $("#tablearea").html(data.html);
    show_raw_data(data);

    const dataset = annotation_set[table_idx].dataset;
    let textType;
    if (dataset == "openweather") {
        textType = "weather forecast";
    } else if (dataset == "ice_hockey") {
        textType = "summary of an ice hockey game";
    } else if (dataset == "gsmarena") {
        textType = "product description";
    } else if (dataset == "wikidata") {
        textType = "graph description";
    } else if (dataset == "owid") {
        textType = "chart caption";
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



function generate_output_box(output) {
    const model = output.model;
    const setup = output.setup.name;

    var label = $('<label>', { class: "label-name" }).text(model);
    var output_box = $('<div>', {
        id: `out-${model}-${setup}`,
        class: `output-box generated-output-box box-${setup} box-${model}`,
    }).append(label);

    if (output.generated == null) {
        return output_box;
    }
    const content = output.generated.replace(/\\n/g, '<br>');

    for (var annotator of ["plain", "gpt-4", "human"]) {
        // add default text
        var placeholder = $('<div>', { id: `out-${model}-${setup}-${annotator}-placeholder`, class: `font-mono out-placeholder out-${annotator}-placeholder` });

        var annotated_content = annotate_content(content, output.annotations, annotator);

        placeholder.html(annotated_content);
        placeholder.hide();
        output_box.append(placeholder);
    }
    return output_box;
}

function annotate_content(content, annotations, annotator) {
    let annotation_to_display = null;
    if (annotator == "gpt-4") {
        // for gpt-4, find the first annotation where the annotator_id begins with gpt-4
        annotation_to_display = annotations.find(a => a.annotator_id.startsWith("gpt-4"));
    } else if (annotator == "human") {
        // for human, find the first annotation where the annotator_id does *not* begin with gpt-4
        annotation_to_display = annotations.find(a => !a.annotator_id.startsWith("gpt-4"));
    }
    if (annotation_to_display == null) {
        // also for plain
        return content;
    }
    let offset = 0; // Track cumulative offset
    const annotationSet = annotation_to_display.annotations;
    // sort by start
    annotationSet.sort(function (a, b) {
        return a.start - b.start;
    });

    var html = content;

    annotationSet.forEach(annotation => {
        const annotationType = annotation.type;
        const color = error_colors[annotationType].color;
        const text = annotation.text;

        const start = annotation.start + offset;
        const end = start + text.length;

        const error_name = error_colors[annotationType].name;
        const reason = annotation.reason;
        let tooltip_text;

        if (annotation.reason !== undefined) {
            tooltip_text = `${error_name} (${reason})`;
        } else {
            tooltip_text = `${error_name}`;
        }

        const spanId = `span-${start}-${end}`;
        const spanContent = `<span id="${spanId}" style="margin-right: 0px;background-color: ${color};" data-bs-toggle="tooltip" data-bs-placement="top" title="${tooltip_text}">${text}</span>`;

        html = html.slice(0, start) + spanContent + html.slice(end);
        // Update the offset
        offset += spanContent.length - text.length;
    });
    return html;
}

function update_displayed_annotations() {
    const annotator = $("#annotations-select").val();

    // hide all placeholders
    $(".out-placeholder").hide();

    // show the selected annotator
    $(`.out-${annotator}-placeholder`).show();

    enable_tooltips();
}

function update_displayed_outputs() {
    const setup_name = $("#setup-select").val();

    // hide all outputs
    $(".generated-output-box").hide();

    // show the selected setup
    $(`.box-${setup_name}`).show();

    $("#setup-name-placeholder").html(setup_name);
    $("#setup-info-placeholder").html("<pre>" + JSON.stringify(setups[setup_name], null, 2) + "</pre>");

}

function create_output_boxes(generated_outputs) {
    // clear the output area
    $("#outputarea").empty();

    // sort outputs by model name
    generated_outputs.sort(function (a, b) {
        return a.model.localeCompare(b.model);
    });

    for (output of generated_outputs) {
        const output_box = generate_output_box(output);
        output_box.appendTo("#outputarea");

    }
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

        show_raw_data(data);
        $("#dataset-spinner").hide();

        total_examples = data.total_examples;
        $("#total-examples").html(total_examples - 1);

        create_output_boxes(data.generated_outputs);
        update_displayed_outputs();
        update_displayed_annotations();
    });
}


$("#dataset-select").on("change", change_dataset);
$("#split-select").on("change", change_split);
$("#setup-select").on("change", update_displayed_outputs);
$("#annotations-select").on("change", update_displayed_annotations);

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

$("#hideOverlayBtn").click(function () {
    $("#overlay-start").fadeOut();
});

function enable_tooltips() {
    // enable tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
}

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

    enable_tooltips();
});