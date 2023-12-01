function add_marker(map, markers, heatmap_points, data) {
    var latlon = new google.maps.LatLng(data.lat, data.lon);
    heatmap_points.push(latlon);
    var infowindow = new google.maps.InfoWindow();
    var marker = new google.maps.Marker({
        position: latlon,
        map: map,
        visible: true,
        title: 'Mushroom'
    });
    marker.addListener('click', function () {
        infowindow.setContent('<img src=' + data.url + '>');
        infowindow.open(map, marker);
        console.log(marker.position.lat(), marker.position.lng(), data.url);
    });
    markers.push(marker);
}
var DefaultRenderer = /** @class */ (function () {
    function DefaultRenderer() {
    }
    /**
     * The default render function for the library used by {@link MarkerClusterer}.
     *
     * Currently set to use the following:
     *
     * ```typescript
     * // change color if this cluster has more markers than the mean cluster
     * const color =
     *   count > Math.max(10, stats.clusters.markers.mean)
     *     ? "#ff0000"
     *     : "#0000ff";
     *
     * // create svg url with fill color
     * const svg = window.btoa(`
     * <svg fill="${color}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240">
     *   <circle cx="120" cy="120" opacity=".6" r="70" />
     *   <circle cx="120" cy="120" opacity=".3" r="90" />
     *   <circle cx="120" cy="120" opacity=".2" r="110" />
     *   <circle cx="120" cy="120" opacity=".1" r="130" />
     * </svg>`);
     *
     * // create marker using svg icon
     * return new google.maps.Marker({
     *   position,
     *   icon: {
     *     url: `data:image/svg+xml;base64,${svg}`,
     *     scaledSize: new google.maps.Size(45, 45),
     *   },
     *   label: {
     *     text: String(count),
     *     color: "rgba(255,255,255,0.9)",
     *     fontSize: "12px",
     *   },
     *   // adjust zIndex to be above other markers
     *   zIndex: 1000 + count,
     * });
     * ```
     */
    DefaultRenderer.prototype.render = function (_a, stats, map) {
        var count = _a.count, position = _a.position;
        // change color if this cluster has more markers than the mean cluster
        var color = "#0000ff";
        // create svg literal with fill color
        var svg = "<svg fill=\"".concat(color, "\" xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 240 240\" width=\"50\" height=\"50\">\n<circle cx=\"120\" cy=\"120\" opacity=\".8\" r=\"70\" visibility=\"visible\" />\n<circle cx=\"120\" cy=\"120\" opacity=\".3\" r=\"90\" visibility=\"visible\" />\n<circle cx=\"120\" cy=\"120\" opacity=\".2\" r=\"110\" visibility=\"visible\" />\n<text x=\"50%\" y=\"50%\" style=\"fill:#fff\" text-anchor=\"middle\" font-size=\"50\" dominant-baseline=\"middle\" font-family=\"roboto,arial,sans-serif\">").concat(count, "</text>\n</svg>");
        var title = "Cluster of ".concat(count, " markers"), 
        // adjust zIndex to be above other markers
        zIndex = Number(google.maps.Marker.MAX_ZINDEX) + count;
        if (markerClusterer.MarkerUtils.isAdvancedMarkerAvailable(map)) {
            // create cluster SVG element
            var parser = new DOMParser();
            var svgEl = parser.parseFromString(svg, "image/svg+xml").documentElement;
            svgEl.setAttribute("transform", "translate(0 25)");
            var clusterOptions_1 = {
                map: map,
                position: position,
                zIndex: zIndex,
                title: title,
                content: svgEl,
            };
            return new google.maps.marker.AdvancedMarkerElement(clusterOptions_1);
        }
        var clusterOptions = {
            position: position,
            zIndex: zIndex,
            title: title,
            icon: {
                url: "data:image/svg+xml;base64,".concat(btoa(svg)),
                anchor: new google.maps.Point(25, 25),
            },
        };
        return new google.maps.Marker(clusterOptions);
    };
    return DefaultRenderer;
}());
function initialize() {
    var heatmap_points = new google.maps.MVCArray;
    var markers = [];
    var centerlatlng = new google.maps.LatLng(60.208067, 30.526095);
    var myOptions = {
        zoom: 4,
        center: centerlatlng,
        mapTypeId: google.maps.MapTypeId.ROADMAP
    };
    var map = new google.maps.Map(document.getElementById("map_canvas"), myOptions);
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
    db.ref('mushrooms').once('value', function (mushrooms) {
        heatmap_points.clear();
        if (markers) {
            for (var i in markers) {
                markers[i].setMap(null);
            }
        }
        mushrooms.forEach(function (snap) {
            data = snap.val();
            add_marker(map, markers, heatmap_points, data);
        });
        var renderer = new DefaultRenderer();
        var markerCluster = new markerClusterer.MarkerClusterer({ markers: markers, map: map, renderer: renderer });
        var startControlDiv = document.createElement('div');
        startControlDiv.setAttribute('horizontal', '');
        startControlDiv.setAttribute('layout', '');
        map.controls[google.maps.ControlPosition.TOP_RIGHT].push(startControlDiv);
    });
    var heatmap = new google.maps.visualization.HeatmapLayer({
        data: heatmap_points
    });
    heatmap.setMap(map);
    heatmap.set('threshold', 10);
    heatmap.set('radius', 30);
    heatmap.set('opacity', 0.600000);
    heatmap.set('dissipating', true);
}
