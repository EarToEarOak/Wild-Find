/*

 Wild Find


 Copyright 2014 - 2017 Al Brown

 Wildlife tracking and mapping


 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License version 2 as published by
 the Free Software Foundation

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
var harrier = new ol.source.Vector();

var view = new ol.View({
	projection : 'EPSG:900913',
	center : [ 0, 0 ],
	zoom : 4
});

var map, gmap;

var styleLocation = new ol.style.Style({
	image : new ol.style.Circle({
		stroke : new ol.style.Stroke({
			color : 'black',
			opacity : 0.2,
			width : 0.5
		}),
		fill : new ol.style.Fill({
			color : 'ff6000'
		}),
		radius : 5
	})
});

var styleLocationSelect = new ol.style.Style({
	image : new ol.style.Circle({
		stroke : new ol.style.Stroke({
			color : 'black',
			opacity : 0.2,
			width : 2
		}),
		fill : new ol.style.Fill({
			color : 'ffa066'
		}),
		radius : 5,
	})
});

var styleHarrier = new ol.style.Style({
	image : new ol.style.RegularShape({
		stroke : new ol.style.Stroke({
			color : 'black',
			opacity : 0.2,
			width : 2
		}),
		fill : new ol.style.Fill({
			color : 'white'
		}),
		radius : 8,
		points: 3,
		angle: 0
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

var layerHarrier = new ol.layer.Vector({
	source : harrier,
	style: styleHarrier
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
	projection : 'EPSG:4326'
});

var overlaySignals = new ol.Overlay({
	autoPan : true,
	autoPanAnimation : {
		duration : 250
	}
});

var keyBing = 'AtgkX0aGPsyJJcv1x9QSyVxqWDJL8B0-bKPnUz3ZDQ0LD0yYbbfhQfux4MPeQUv1';
var keyGoogle = 'AIzaSyBP_bgnvfcQH4Rgd52HOHDuPpqwTWE2qfw';

function init() {
	_initOpenLayers();

	var script = document.createElement('script');
	script.type = 'text/javascript';
	script.src = 'https://maps.googleapis.com/maps/api/js?v=3.exp&callback=_initGoogleMaps&key='
			+ keyGoogle;
	document.body.appendChild(script);

	_addLayers();
	map.addLayer(layerHeatmap);
	map.addLayer(layerTrack);
	map.addLayer(layerLocations);
	map.addLayer(layerHarrier);
	_setLayerByName('OpenStreetMap');
	_sendLayerNames();
}

function _initOpenLayers() {
	layers.push(new ol.layer.Tile({
		name : 'Bing Aerial',
		source : new ol.source.BingMaps({
			key : keyBing,
			imagerySet : 'Aerial',
			maxZoom : 19
		})
	}));

	layers.push(new ol.layer.Tile({
		name : 'Bing Aerial with Labels',
		source : new ol.source.BingMaps({
			key : keyBing,
			imagerySet : 'AerialWithLabels',
			maxZoom : 19
		})
	}));

	layers.push(new ol.layer.Tile({
		name : 'Bing Ordnance Survey',
		source : new ol.source.BingMaps({
			key : keyBing,
			imagerySet : 'ordnanceSurvey',
			culture : 'en-gb',
			maxZoom : 17
		})
	}));

	layers.push(new ol.layer.Tile({
		name : 'Bing Road',
		source : new ol.source.BingMaps({
			key : keyBing,
			imagerySet : 'Road',
			maxZoom : 19
		})
	}));

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
		name : 'OpenStreetMap',
		source : new ol.source.OSM()
	}));

	var controls = ol.control.defaults();
	controls.extend([ controlScale, controlPos ]);

	map = new ol.Map({
		target : 'olMap',
		view : view,
		controls : controls,
		overlays : [ overlaySignals ],
		loadTilesWhileInteracting : true
	});

	map.setView(view);

	map.on('singleclick', _popup);
	map.addInteraction(dragBox);
	dragBox.on('boxend', selectLocations);

	_setListeners(true);
}

function _initGoogleMaps() {
	gmap = new google.maps.Map(document.getElementById('gMap'), {
		disableDefaultUI : true,
		keyboardShortcuts : false,
		draggable : false,
		disableDoubleClickZoom : true,
		scrollwheel : false,
		streetViewControl : false,
		center : {
			lat : 0,
			lng : 0
		}
	});

	view.on('change:center', function() {
		var centre = ol.proj.transform(view.getCenter(), 'EPSG:900913',
				'EPSG:4326');
		gmap.setCenter(new google.maps.LatLng(centre[1], centre[0]));
	});
	view.on('change:resolution', function() {
		var zoom = view.getZoom();
		if (zoom > 21) {
			zoom = 21;
			view.setZoom(zoom);
		}
		gmap.setZoom(zoom);
		gmap.setTilt(0);
	});

	var layer;

	layer = new ol.layer.Group({
		name : 'Google Hybrid',
		id : google.maps.MapTypeId.HYBRID
	});
	map.addLayer(layer);
	layers.push(layer);

	layer = new ol.layer.Group({
		name : 'Google Road',
		id : google.maps.MapTypeId.ROADMAP
	});
	map.addLayer(layer);
	layers.push(layer);

	layer = new ol.layer.Group({
		name : 'Google Satellite',
		id : google.maps.MapTypeId.SATELLITE
	});
	map.addLayer(layer);
	layers.push(layer);

	layer = new ol.layer.Group({
		name : 'Google Terrain',
		id : google.maps.MapTypeId.TERRAIN
	});
	map.addLayer(layer);
	layers.push(layer);

	_sendLayerNames();
}

function _addLayers() {
	for (var i = 0; i < layers.length; i++)
		map.addLayer(layers[i]);
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
	if (typeof mapLink != "undefined")
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

function _setLayerByName(name) {
	var i = 0;

	for (i = 0; i < layers.length; i++)
		if (layers[i].get('name').indexOf(name) > -1)
			break;

	setLayer(i);
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

function getPos() {
	var pos = view.getCenter();
	var zoom = view.getZoom();

	return [ pos, zoom ];
}

function getLayer() {
	for (var i = 0; i < layers.length; i++)
		if (layers[i].getVisible())
			return i;

	return 0;
}

function setPos(lon, lat, zoom) {
	view.setZoom(zoom);
	view.setCenter([ lon, lat ]);
}

function setLayer(index) {
	for (var i = 0; i < layers.length; i++)
		layers[i].setVisible(false);

	var layer = layers[index];
	layer.setVisible(true);

	var gLayer = layer.get('name').indexOf('Google') > -1;
	var gMapDiv = document.getElementById('gMap');
	if (gLayer) {
		gMapDiv.style.visibility = 'visible';
		gmap.setMapTypeId(layer.get('id'));
	} else
		gMapDiv.style.visibility = 'hidden';
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

function setHarrier(lon, lat) {
	var point = new ol.geom.Point([ lon, lat ]);
	point.transform('EPSG:4326', 'EPSG:900913');

	var feature = new ol.Feature({
		geometry : point,
//		style: styleHarrier
	});
	clearHarrier();
	harrier.addFeature(feature);
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
}

function clearHarrier() {
	harrier.clear(true);
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
	var extentLoc = locations.getExtent();
	var extentHar = harrier.getExtent();
	var extent = ol.extent.extend(extentLoc, extentHar);

	_setListeners(false);
	view.fitExtent(extent, map.getSize());
	_setListeners(true);
}

function transformCoord(lon, lat) {
	var point = new ol.geom.Point([ lon, lat ]);
	point.transform('EPSG:4326', 'EPSG:900913');

	return point.getCoordinates();
}
