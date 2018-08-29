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

        modifyVar(markersVisibility, !markersVisibility.valueOf())
        var arrayLength = markers.length;
        for (var i = 0; i < arrayLength; i++) {
            markers[i].setVisible(markersVisibility.valueOf());
        }
    });
}

function modifyVar(obj, val) {
  obj.valueOf = obj.toSource = obj.toString = function(){ return val; };
}

function add_marker(map, markers, markersVisibility, heatmap_points, data) {
    latlon = new google.maps.LatLng(data.lat, data.lon)
    heatmap_points.push(latlon)

    var infowindow = new google.maps.InfoWindow();

    var marker = new google.maps.Marker({
      position: latlon,
      map: map,
      visible: markersVisibility.valueOf(),
      title: 'Mushroom'
    });

    marker.addListener('click', function() {
      infowindow.setContent('<img src=' + data.url + '>');
      infowindow.open(map, marker);
      console.log(marker.position.lat(), marker.position.lng(), data.url);
    });
    markers.push(marker);
}

function initialize() {
    var heatmap_points = new google.maps.MVCArray;
    var markers = [];
    var markersVisibility = new Boolean(true);

    var centerlatlng = new google.maps.LatLng(60.208067, 30.526095);

	var myOptions = {
		zoom: 16,
		center: centerlatlng,
		mapTypeId: google.maps.MapTypeId.ROADMAP
	};

	map = new google.maps.Map(document.getElementById("map_canvas"), myOptions);

    var config = {
        apiKey: "AIzaSyDvLeix43yIMGr6bjkG6ccDeiB-e7qDxHc",
        authDomain: "geomushroom-186520.firebaseapp.com",
        databaseURL: "https://geomushroom-186520.firebaseio.com",
        storageBucket: "geomushroom-186520.appspot.com",
        serviceAccount: "geomushroom-34720f274ce5.json"
    };
    firebase.initializeApp(config);

      // Get a reference to the database service
    var db = firebase.database();
    db.ref('mushrooms').once('value', function(mushrooms) {
        heatmap_points.clear();
        if (markers) {
             for (var i in markers) {
                 markers[i].setMap(null);
            }
        }

        mushrooms.forEach(function(snap) {
            data = snap.val();
            add_marker(map, markers, markersVisibility, heatmap_points, data);
        });
    });
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

    hideMarkers(startControlDiv, markers, markersVisibility);
    map.controls[google.maps.ControlPosition.TOP_RIGHT].push(startControlDiv);
}
