/*

 Project Peregrine


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

view = new ol.View({
	projection : 'EPSG:900913',
	center : [ 0, 0 ],
	zoom : 4
});

locations = new ol.source.Vector();
layerLocations = new ol.layer.Vector({
	source : locations,
	style : new ol.style.Style({
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
	})
});

layerHeatmap = new ol.layer.Image({
	opacity : 0.6
})

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

	map = new ol.Map({
		target : 'map',
		view : view,
		layers : layers
	});

	map.addLayer(layerHeatmap)
	map.addLayer(layerLocations)

	setListeners(true);

	setLayer(layers.length - 1);
	sendLayerNames();
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

function addLocations(lon, lat) {
	point = new ol.geom.Point([ lon, lat ]);
	point.transform('EPSG:4326', 'EPSG:900913');

	feature = new ol.Feature({
		geometry : point
	});

	locations.addFeature(feature);
}

function clear() {
	locations.clear();
	layerHeatmap.setSource(null)
}

function setHeatmap(north, south, east, west) {
	extent = [ west, south, east, north ]

	url = '/heatmap.png?a=' + Math.random() * 1000000;
	source = new ol.source.ImageStatic({
		url : url,
		imageExtent : extent
	});

	layerHeatmap.setSource(source)
}

function showLocations(show) {
	layerLocations.setVisible(show);
}

function showHeatmap(show) {
	layerHeatmap.setVisible(show);
}

function setOpacity(opacity){
	layerHeatmap.setOpacity(opacity)
}

function follow() {
	setListeners(false);
	extent = locations.getExtent();
	view.fitExtent(extent, map.getSize());
	setListeners(true);
}
