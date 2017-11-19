var interest_polygon = [
          {lat: 59.157162, lng: 28.066060},
          {lat: 60.571626, lng: 28.066060},
          {lat: 60.571626, lng: 31.536363},
          {lat: 59.157162, lng: 31.536363},
          {lat: 59.157162, lng: 28.066060}];
var heatmap_points = [];
/**
   * The CenterControl adds a control to the map that recenters the map on
   * Chicago.
   * This constructor takes the control DIV as an argument.
   * @constructor
   */
function StartControl(controlDiv, map, socket) {
    // Set CSS for the control border.
    var controlUI = document.createElement('div');
    controlUI.style.backgroundColor = '#fff';
    controlUI.style.border = '2px solid #fff';
    controlUI.style.borderRadius = '3px';
    controlUI.style.boxShadow = '0 2px 6px rgba(0,0,0,.3)';
    controlUI.style.cursor = 'pointer';
    controlUI.style.marginBottom = '22px';
    controlUI.style.textAlign = 'center';
    controlUI.title = 'Click to start retreiving data';
    controlDiv.appendChild(controlUI);

    // Set CSS for the control interior.
    var controlText = document.createElement('div');
    controlText.style.color = 'rgb(25,25,25)';
    controlText.style.fontFamily = 'Roboto,Arial,sans-serif';
    controlText.style.fontSize = '16px';
    controlText.style.lineHeight = '38px';
    controlText.style.paddingLeft = '5px';
    controlText.style.paddingRight = '5px';
    controlText.innerHTML = 'Start';
    controlUI.appendChild(controlText);

    // Setup the click event listeners: simply set the map to Chicago.
    controlUI.addEventListener('click', function() {
    socket.send('Start\n');

    if (controlText.innerHTML == "Start") {
        controlText.innerHTML = "Stop";
    } else {
        controlText.innerHTML = "Start";
    }
  });

}

function LoadLocalDataControl(controlDiv, map, socket) {
    // Set CSS for the control border.
    var controlUI = document.createElement('div');
    controlUI.style.backgroundColor = '#fff';
    controlUI.style.border = '2px solid #fff';
    controlUI.style.borderRadius = '3px';
    controlUI.style.boxShadow = '0 2px 6px rgba(0,0,0,.3)';
    controlUI.style.cursor = 'pointer';
    controlUI.style.marginBottom = '22px';
    controlUI.style.textAlign = 'center';
    controlUI.title = 'Click to load locally stored data';
    controlDiv.appendChild(controlUI);

    // Set CSS for the control interior.
    var controlText = document.createElement('div');
    controlText.style.color = 'rgb(25,25,25)';
    controlText.style.fontFamily = 'Roboto,Arial,sans-serif';
    controlText.style.fontSize = '16px';
    controlText.style.lineHeight = '38px';
    controlText.style.paddingLeft = '5px';
    controlText.style.paddingRight = '5px';
    controlText.innerHTML = 'Load Local Data';
    controlUI.appendChild(controlText);

    // Setup the click event listeners: simply set the map to Chicago.
    controlUI.addEventListener('click', function() {
      socket.send('Bitch\n');
    });

}

function StopControl(controlDiv, map, socket) {
    // Set CSS for the control border.
    var controlUI = document.createElement('div');
    controlUI.style.backgroundColor = '#fff';
    controlUI.style.border = '2px solid #fff';
    controlUI.style.borderRadius = '3px';
    controlUI.style.boxShadow = '0 2px 6px rgba(0,0,0,.3)';
    controlUI.style.cursor = 'pointer';
    controlUI.style.marginBottom = '22px';
    controlUI.style.textAlign = 'center';
    controlUI.title = 'Click to load locally stored data';
    controlDiv.appendChild(controlUI);

    // Set CSS for the control interior.
    var controlText = document.createElement('div');
    controlText.style.color = 'rgb(25,25,25)';
    controlText.style.fontFamily = 'Roboto,Arial,sans-serif';
    controlText.style.fontSize = '16px';
    controlText.style.lineHeight = '38px';
    controlText.style.paddingLeft = '5px';
    controlText.style.paddingRight = '5px';
    controlText.innerHTML = 'Stop';
    controlUI.appendChild(controlText);

    // Setup the click event listeners: simply set the map to Chicago.
    controlUI.addEventListener('click', function() {
      socket.send('Stop\n');
    });

}



function initialize() {
    // create websocket
    if (! ("WebSocket" in window)) WebSocket = MozWebSocket; // firefox
    var socket = new WebSocket("ws://localhost:8076");

    // open the socket
    socket.onopen = function(event) {
    socket.send('connected\n');
    // show server response
    socket.onmessage = function(e) {
        document.getElementById("entry").value = e.data;
    }

    // for each typed key send #entry's text to server
    document.getElementById("entry").onkeyup = (function (e) {
        socket.send(document.getElementById("entry").value+"\n");
    });
    }


	try {
		
		var centerlatlng = new google.maps.LatLng(60.208067, 30.526095);
	} catch (err) {
		alert(err);
	}
	
	var myOptions = {
		zoom: 16,
		center: centerlatlng,
		mapTypeId: google.maps.MapTypeId.ROADMAP
	};

	map = new google.maps.Map(document.getElementById("map_canvas"), myOptions);


	heatmap_points = [
	new google.maps.LatLng(60.208067, 30.526095),
	new google.maps.LatLng(60.036650, 30.389375),
	new google.maps.LatLng(60.045336, 30.321285)];

     // Construct the polygon.
    var bermudaTriangle = new google.maps.Polygon({
      paths: interest_polygon,
      strokeColor: '#FF0000',
      strokeOpacity: 0.8,
      strokeWeight: 2,
      fillColor: '#FF0000',
      draggable: true,
      fillOpacity: 0.35,
      geodesic: true,
      editable: true
    });
    bermudaTriangle.setMap(map);

   	google.maps.event.addListener(bermudaTriangle, "dragend", getPolygonCoords);
    google.maps.event.addListener(bermudaTriangle.getPath(), "insert_at", getPolygonCoords);
    google.maps.event.addListener(bermudaTriangle.getPath(), "remove_at", getPolygonCoords);
    google.maps.event.addListener(bermudaTriangle.getPath(), "set_at", getPolygonCoords);

	function getPolygonCoords() {
       	var len = bermudaTriangle.getPath().getLength();
       	var htmlStr = "";
        for (var i = 0; i < len; i++) {
            htmlStr += bermudaTriangle.getPath().getAt(i).toUrlValue(5) + "\n";
        }
        //alert(htmlStr);
    }   

	var pointArray = new google.maps.MVCArray(heatmap_points);
	var heatmap;
	heatmap = new google.maps.visualization.HeatmapLayer({
		data: pointArray
	});

	function placeMarkerAndPanTo(latLng, map) {
	  var marker = new google.maps.Marker({
	    position: latLng,
	    map: map
	  });
	}

	map.addListener('click', function(e) {
	    placeMarkerAndPanTo(e.latLng, map);
	    window.alert(e.latLng);
	  });

	var contentString = '<div id="content">'+
      '<div id="siteNotice">'+
      '</div>'+
      '<h1 id="firstHeading" class="firstHeading">Uluru</h1>'+
      '<div id="bodyContent">'+
      '<p><b>Uluru</b>, also referred to as <b>Ayers Rock</b>, is a large ' +
      'sandstone rock formation in the southern part of the '+
      'Northern Territory, central Australia. It lies 335&#160;km (208&#160;mi) '+
      'south west of the nearest large town, Alice Springs; 450&#160;km '+
      '(280&#160;mi) by road. Kata Tjuta and Uluru are the two major '+
      'features of the Uluru - Kata Tjuta National Park. Uluru is '+
      'sacred to the Pitjantjatjara and Yankunytjatjara, the '+
      'Aboriginal people of the area. It has many springs, waterholes, '+
      'rock caves and ancient paintings. Uluru is listed as a World '+
      'Heritage Site.</p>'+
      '<p>Attribution: Uluru, <a href="https://en.wikipedia.org/w/index.php?title=Uluru&oldid=297882194">'+
      'https://en.wikipedia.org/w/index.php?title=Uluru</a> '+
      '(last visited June 22, 2009).</p>'+
      '</div>'+
      '</div>';

    var infowindow = new google.maps.InfoWindow({
      content: contentString
    });

    var marker = new google.maps.Marker({
      position: heatmap_points[0],
      map: map,
      visible: false,
      title: 'Uluru (Ayers Rock)'
    });
    marker.addListener('click', function() {
      infowindow.open(map, marker);
    });

  	heatmap.setMap(map);
  	heatmap.set('threshold', 10);
  	heatmap.set('radius', 30);
  	heatmap.set('opacity', 0.600000);
  	heatmap.set('dissipating', true);



    var startControlDiv = document.createElement('div');
    startControlDiv.setAttribute('horizontal', '');
    startControlDiv.setAttribute('layout', '');
    var startControl = new StartControl(startControlDiv, map, socket);
    var loadControl = new LoadLocalDataControl(startControlDiv, map, socket);
    map.controls[google.maps.ControlPosition.TOP_RIGHT].push(startControlDiv);
}
