/*

 Wild Find


 Copyright 2014 - 2015 Al Brown

 Wildlife tracking and mapping


 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, or (at your option)
 any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.

 */

layers = [];

locations = new ol.source.Vector();
track = new ol.source.Vector();

view = new ol.View({
	projection : 'EPSG:900913',
	center : [ 0, 0 ],
	zoom : 4
});

styleLocation = new ol.style.Style({
	image : new ol.style.Circle({
		stroke : new ol.style.Stroke({
			color : 'black',
			opacity : 0.2,
			width : 0.5
		}),
		radius : 5,
		fill : new ol.style.Fill({
			color : 'ff6000'
		})
	})
});

layerLocations = new ol.layer.Vector({
	source : locations,
	style : styleLocation
});

layerTrack = new ol.layer.Vector({
	source : track,
	style : new ol.style.Style({
		stroke : new ol.style.Stroke({
			color : 'dd6300',
			width : 3
		})
	})
});

layerHeatmap = new ol.layer.Image({
	opacity : 0.6
})

dragBox = new ol.interaction.DragBox({
	condition : ol.events.condition.shiftKeyOnly,
	layers : [ layerLocations ],
	style : new ol.style.Style({
		stroke : new ol.style.Stroke({
			color : '0066FF'
		})
	})
});

function init() {
	layers.push(new ol.layer.Tile({
		name : 'MapQuest Satellite',
		source : new ol.source.MapQuest({
			layer : 'sat'
		})
	}));

	layers.push(new ol.layer.Tile({
		name : 'MapQuest OSM',
		source : new ol.source.MapQuest({
			layer : 'osm'
		})
	}));

	layers.push(new ol.layer.Tile({
		name : 'MapQuest Hybrid',
		source : new ol.source.MapQuest({
			layer : 'hyb'
		})
	}));

	layers.push(new ol.layer.Tile({
		name : 'OpenStreetMap',
		source : new ol.source.OSM()
	}));

	controlScale = new ol.control.ScaleLine();
	controls = ol.control.defaults();
	controls.extend([ controlScale ]);

	map = new ol.Map({
		target : 'map',
		view : view,
		layers : layers,
		controls : controls
	});

	map.addLayer(layerHeatmap)
	map.addLayer(layerTrack)
	map.addLayer(layerLocations)

	map.addInteraction(dragBox);
	dragBox.on('boxend', selectLocations);

	setListeners(true);

	setLayer(layers.length - 1);
	sendLayerNames();
	showBusy(false);
}

function setListeners(enable) {
	if (enable) {
		map.on('pointerdrag', onInteraction);
		view.on('change:resolution', onInteraction);
	} else {
		map.un('pointerdrag', onInteraction);
		view.un('change:resolution', onInteraction);
	}
}

function onInteraction() {
	mapLink.on_interaction();
}

function sendLayerNames() {
	if (typeof mapLink === "undefined")
		return;

	names = [];

	for (var i = 0; i < layers.length; i++)
		names.push(layers[i].get('name'));

	mapLink.on_layer_names(JSON.stringify(names));
}

function transformCoord(lon, lat) {
	point = new ol.geom.Point([ lon, lat ]);
	point.transform('EPSG:4326', 'EPSG:900913');

	return point.getCoordinates();
}

function getLayer() {
	for (var i = 0; i < layers.length; i++)
		if (layers[i].getVisible())
			return i;

	return 0;
}

function setLayer(index) {
	for (var i = 0; i < layers.length; i++)
		layers[i].setVisible(false);

	layers[index].setVisible(true);
}

function addLocation(freq, lon, lat) {
	point = new ol.geom.Point([ lon, lat ]);
	point.transform('EPSG:4326', 'EPSG:900913');
	coord = ol.proj.transform([ lon, lat ], 'EPSG:4326', 'EPSG:900913');

	console.log(freq);
	feature = new ol.Feature({
		name : freq,
		geometry : point
	});
	locations.addFeature(feature);

	line = track.getFeatures();
	if (line.length == 0) {
		feature = new ol.Feature({
			geometry : new ol.geom.LineString([], 'XY')
		});
		track.addFeature(feature);
		feature.getGeometry().appendCoordinate(coord);
	} else
		line[0].getGeometry().appendCoordinate(coord);
}

function selectLocations() {
	frequencies = []

	extent = dragBox.getGeometry().getExtent();
	source = layerLocations.getSource();

	source.forEachFeature(function(feature) {
		coords = feature.getGeometry().getCoordinates();
		if (ol.extent.containsCoordinate(extent, coords))
			frequencies.push(feature.get('name'))
		else
			feature.setStyle(styleLocation);
	});

	mapLink.on_selected(JSON.stringify(frequencies));
}

function clearLocations() {
	locations.clear();
	track.clear();
}

function setHeatmap(north, south, east, west) {
	extent = [ west, south, east, north ]

	loadFunction = function(image, src) {
		element = image.getImage();
		element.src = src;
		element.onload = function() {
			showBusy(false);
		};
	}

	url = '/heatmap.png?a=' + Math.random() * 1000000;
	source = new ol.source.ImageStatic({
		url : url,
		imageExtent : extent,
		imageLoadFunction : loadFunction
	});

	layerHeatmap.setSource(source)
}

function clearHeatmap() {
	layerHeatmap.setSource(null)
	showBusy(false);
}

function showBusy(show) {
	display = 'none';
	if (show)
		display = 'block';

	document.getElementById('busy').style.display = display;
}

function showLocations(show) {
	layerLocations.setVisible(show);
}

function showTrack(show) {
	layerTrack.setVisible(show);
}

function showHeatmap(show) {
	layerHeatmap.setVisible(show);
}

function setOpacity(opacity) {
	layerHeatmap.setOpacity(opacity)
}

function follow() {
	setListeners(false);
	extent = locations.getExtent();
	view.fitExtent(extent, map.getSize());
	setListeners(true);
}
