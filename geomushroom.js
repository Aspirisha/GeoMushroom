function getInterestRegionStr(searchPolygon) {
    var len = searchPolygon.getPath().getLength();
    var htmlStr = "";
    for (var i = 0; i < len; i++) {
        htmlStr += searchPolygon.getPath().getAt(i).toUrlValue(5) + ";";
    }
    return htmlStr;
}


function addButtonBase(controlDiv, title, text) {
    var controlUI = document.createElement('div');
    controlUI.style.backgroundColor = '#fff';
    controlUI.style.border = '2px solid #fff';
    controlUI.style.borderRadius = '3px';
    controlUI.style.boxShadow = '0 2px 6px rgba(0,0,0,.3)';
    controlUI.style.cursor = 'pointer';
    controlUI.style.marginBottom = '22px';
    controlUI.style.textAlign = 'center';
    controlUI.title = title; //'Click to hide markers';
    controlDiv.appendChild(controlUI);

    // Set CSS for the control interior.
    var controlText = document.createElement('div');
    controlText.style.color = 'rgb(25,25,25)';
    controlText.style.fontFamily = 'Roboto,Arial,sans-serif';
    controlText.style.fontSize = '16px';
    controlText.style.lineHeight = '38px';
    controlText.style.paddingLeft = '5px';
    controlText.style.paddingRight = '5px';
    controlText.innerHTML = text; //'Hide Markers';
    controlUI.appendChild(controlText);

    return [controlUI, controlText];
}

function updateControl(controlDiv, searchPolygon, socket, heatmap_points, markers, map) {
    var res = addButtonBase(controlDiv, 'Update map with new ROI', 'Update');
    var controlUI = res[0];
    var controlText = res[1];

    controlUI.addEventListener('click', function() {
        try {
        var command = 'Update ' + getInterestRegionStr(searchPolygon) + "\n";
        heatmap_points.clear();
        if (markers) {
            for (var i in markers) {
                markers[i].setMap(null);
            }
        }
        markers.length = 0;
        socket.send(command);
    } catch (err) {alert(err);}
  });

}

function hideMarkers(controlDiv, markers, markersVisibility) {
    var res = addButtonBase(controlDiv, 'Click to hide or show markers', 'Hide Markers');
    var controlUI = res[0];
    var controlText = res[1];

    controlUI.addEventListener('click', function() {
        if (controlText.innerHTML == "Show Markers") {
            controlText.innerHTML = "Hide Markers";
        } else {
            controlText.innerHTML = "Show Markers";
        }

        markersVisibility = !markersVisibility;
        var arrayLength = markers.length;
        for (var i = 0; i < arrayLength; i++) {
            markers[i].setVisible(markersVisibility);
        }
    });
}

function hideROI(controlDiv, polygon) {
    var res = addButtonBase(controlDiv, 'Click to hide or show ROI', 'Hide ROI');
    var controlUI = res[0];
    var controlText = res[1];

    // Setup the click event listeners: simply set the map to Chicago.
    controlUI.addEventListener('click', function() {
        var visible = true;
        if (controlText.innerHTML == "Show ROI") {
            controlText.innerHTML = "Hide ROI";
        } else {
            visible = false;
            controlText.innerHTML = "Show ROI";
        }
        polygon.setVisible(visible);
    });
}


function initialize() {
    // create websocket
    if (!("WebSocket" in window)) {
        WebSocket = MozWebSocket; // firefox
    }

    var socket = new WebSocket("ws://localhost:8076");
    var heatmap_points = new google.maps.MVCArray;
    var markers = [];
    var markersVisibility = true;

    socket.onopen = function(event) {
        socket.onmessage = function(e) {
            params = e.data.split(' ');
            if (params[0] == "LATLONS") {
                lat = parseFloat(params[1]);
                lon = parseFloat(params[2]);
                url = params[3];
                heatmap_points.push(new google.maps.LatLng(lat, lon))

                var contentString = `<img src="${url}" alt="Mountain View">`;

                var infowindow = new google.maps.InfoWindow({
                  content: contentString
                });

                var marker = new google.maps.Marker({
                  position: new google.maps.LatLng(lat, lon),
                  map: map,
                  visible: markersVisibility,
                  title: 'Mushroom'
                });
                marker.addListener('click', function() {
                  infowindow.open(map, marker);
                });
                markers.push(marker);
            }
        }
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

     // Construct the polygon.
     var default_interest_polygon = [
          {lat: 59.157162, lng: 28.066060},
          {lat: 60.571626, lng: 28.066060},
          {lat: 60.571626, lng: 31.536363},
          {lat: 59.157162, lng: 31.536363},
          {lat: 59.157162, lng: 28.066060}];

    var searchPolygon = new google.maps.Polygon({
      paths: default_interest_polygon,
      strokeColor: '#FF0000',
      strokeOpacity: 0.8,
      strokeWeight: 2,
      fillColor: '#FF0000',
      draggable: true,
      fillOpacity: 0.35,
      geodesic: true,
      editable: true
    });
    searchPolygon.setMap(map);

	var heatmap = new google.maps.visualization.HeatmapLayer({
		data: heatmap_points
	});

    heatmap.setMap(map);
  	heatmap.set('threshold', 10);
  	heatmap.set('radius', 30);
  	heatmap.set('opacity', 0.600000);
  	heatmap.set('dissipating', true);

    var startControlDiv = document.createElement('div');
    startControlDiv.setAttribute('horizontal', '');
    startControlDiv.setAttribute('layout', '');
    updateControl(startControlDiv, searchPolygon, socket, heatmap_points, markers, map);
    hideMarkers(startControlDiv, markers, markersVisibility);
    hideROI(startControlDiv, searchPolygon);
    map.controls[google.maps.ControlPosition.TOP_RIGHT].push(startControlDiv);
}
