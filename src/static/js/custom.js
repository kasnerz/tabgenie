
$("#next-btn").click(function() {
    alert("Handler for .click() called.");
  }
);


function nextbtn(){
    $.get("/table", { inc: 1 }, function(data) {
        $("#tablearea").html( data );
      });
}

function prevbtn(){
    $.get("/table", { inc: -1 }, function(data) {
        $("#tablearea").html( data );
      });
}
