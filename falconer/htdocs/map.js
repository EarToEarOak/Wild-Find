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

"use strict";

var layers = [];

var locations = new ol.source.Vector();
var track = new ol.source.Vector();

var view = new ol.View({
	projection : 'EPSG:900913',
	center : [ 0, 0 ],
	zoom : 4
});

var map;

var styleLocation = new ol.style.Style({
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

var styleLocationSelect = new ol.style.Style({
	image : new ol.style.Circle({
		stroke : new ol.style.Stroke({
			color : 'black',
			opacity : 0.2,
			width : 2
		}),
		radius : 5,
		fill : new ol.style.Fill({
			color : 'ffa066'
		})
	})
});

var layerLocations = new ol.layer.Vector({
	source : locations,
	style : styleLocation
});

var layerTrack = new ol.layer.Vector({
	source : track,
	style : new ol.style.Style({
		stroke : new ol.style.Stroke({
			color : 'dd6300',
			width : 3
		})
	})
});

var layerHeatmap = new ol.layer.Image({
	opacity : 0.6
});

var dragBox = new ol.interaction.DragBox({
	condition : ol.events.condition.shiftKeyOnly,
	layers : [ layerLocations ],
	style : new ol.style.Style({
		stroke : new ol.style.Stroke({
			color : '003d99'
		})
	})
});

var controlScale = new ol.control.ScaleLine();

var controlPos = new ol.control.MousePosition({
	coordinateFormat : ol.coordinate.createStringXY(5),
	projection : 'EPSG:4326',
	undefinedHTML : '&nbsp;'
});

var overlaySignals = new ol.Overlay({
	autoPan : true,
	autoPanAnimation : {
		duration : 250
	}
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

	var controls = ol.control.defaults();
	controls.extend([ controlScale, controlPos ]);

	map = new ol.Map({
		target : 'map',
		view : view,
		layers : layers,
		controls : controls,
		overlays : [ overlaySignals ]
	});

	map.addLayer(layerHeatmap);
	map.addLayer(layerTrack);
	map.addLayer(layerLocations);

	map.setView(view);

	map.on('singleclick', _popup);
	map.addInteraction(dragBox);
	dragBox.on('boxend', selectLocations);

	_setListeners(true);

	setLayer(layers.length - 1);
	_sendLayerNames();
	showBusy(false);
}

function _setListeners(enable) {
	if (enable) {
		map.on('pointerdrag', _onInteraction);
		view.on('change:resolution', _onInteraction);
	} else {
		map.un('pointerdrag', _onInteraction);
		view.un('change:resolution', _onInteraction);
	}
}

function _onInteraction() {
	mapLink.on_interaction();
}

function _sendLayerNames() {
	if (typeof mapLink === "undefined")
		return;

	var names = [];

	for (var i = 0; i < layers.length; i++)
		names.push(layers[i].get('name'));

	mapLink.on_layer_names(JSON.stringify(names));
}

function _popup(event) {
	var features = [];

	map.forEachFeatureAtPixel(event.pixel, function(feature, layer) {
		if (layer == layerLocations)
			features.push(feature);
	});

	var element = document.getElementById('popup');
	overlaySignals.setElement(element);

	if (features.length === 0)
		overlaySignals.setPosition(undefined);
	else {
		var coordsFeature = features[0].getGeometry().getCoordinates();
		coordsFeature = ol.proj.transform(coordsFeature, 'EPSG:900913',
				'EPSG:4326');
		var location = ol.coordinate.toStringXY(coordsFeature, 5);

		var frequencies = [];
		for (var i = 0; i < features.length; i++) {
			var feature = features[i];
			frequencies.push([ feature.get('name'), feature.get('rate'),
					feature.get('level') ]);
		}
		var sigList = frequencies.filter(function(item, pos, self) {
			return self.indexOf(item) == pos;
		});
		sigList.sort();

		var info = '<h4>Location</h4>';
		info += location;
		info += '<h4>Signals</h4>';
		info += '<table class="SigTable">';
		info += '<tr>';
		info += '<th>Freq<br/>(MHz)</th>';
		info += '<th>Rate<br/>(PPM)</th>';
		info += '<th>Level<br/>(dB)</th>';
		info += '</tr>';
		for (var i = 0; i < sigList.length; i++) {
			var freq = sigList[i][0] / 1000000;
			info += '<tr><td>';
			info += freq.toFixed(4);
			info += '</td><td>';
			info += sigList[i][1];
			info += '</td><td>';
			info += sigList[i][2];
			info += '</tr></td>';
		}
		info += '</table>';

		element.innerHTML = info;

		var coords = event.coordinate;
		overlaySignals.setPosition(coords);
	}
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

function setUnits(units) {
	controlScale.setUnits(units);
}

function setHeatmap(north, south, east, west) {
	var extent = [ west, south, east, north ];

	var loadFunction = function(image, src) {
		var element = image.getImage();
		element.src = src;
		element.onload = function() {
			showBusy(false);
		};
	};

	var url = '/heatmap.png?a=' + Math.random() * 1000000;
	var source = new ol.source.ImageStatic({
		url : url,
		imageExtent : extent,
		imageLoadFunction : loadFunction
	});

	layerHeatmap.setSource(source);
}

function setHeatmapOpacity(opacity) {
	layerHeatmap.setOpacity(opacity);
}

function addLocation(freq, rate, level, lon, lat) {
	var point = new ol.geom.Point([ lon, lat ]);
	point.transform('EPSG:4326', 'EPSG:900913');

	var coord = ol.proj.transform([ lon, lat ], 'EPSG:4326', 'EPSG:900913');

	var feature = new ol.Feature({
		name : freq,
		rate : rate,
		level : level,
		geometry : point
	});
	locations.addFeature(feature);

	var line = track.getFeatures();
	if (line.length === 0) {
		feature = new ol.Feature({
			geometry : new ol.geom.LineString([], 'XY')
		});
		track.addFeature(feature);
		feature.getGeometry().appendCoordinate(coord);
	} else
		line[0].getGeometry().appendCoordinate(coord);
}

function selectLocations() {
	var frequencies = [];

	var extent = dragBox.getGeometry().getExtent();
	var source = layerLocations.getSource();

	source.forEachFeature(function(feature) {
		var coords = feature.getGeometry().getCoordinates();
		if (ol.extent.containsCoordinate(extent, coords)) {
			frequencies.push(feature.get('name'));
			feature.setStyle(styleLocationSelect);
		} else
			feature.setStyle(styleLocation);
	});

	mapLink.on_selected(JSON.stringify(frequencies));
}

function selectLocation(freq, selected) {
	var source = layerLocations.getSource();

	source.forEachFeature(function(feature) {
		if (feature.get('name') == freq)
			if (selected) {
				feature.setStyle(styleLocationSelect);
				feature.getStyle().setZIndex(99);
			} else {
				feature.setStyle(styleLocation);
				feature.getStyle().setZIndex(0);
			}
	});
}

function clearLocations() {
	locations.clear();
	track.clear();
}

function clearHeatmap() {
	layerHeatmap.setSource(null);
	showBusy(false);
}

function showBusy(show) {
	var display = 'none';
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

function follow() {
	var extent = locations.getExtent();

	_setListeners(false);
	view.fitExtent(extent, map.getSize());
	_setListeners(true);
}

function transformCoord(lon, lat) {
	var point = new ol.geom.Point([ lon, lat ]);
	point.transform('EPSG:4326', 'EPSG:900913');

	return point.getCoordinates();
}
