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

function init() {

	view = new ol.View({
		projection : 'EPSG:900913',
		center : [ 0, 0 ],
		zoom : 4
	});

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

	map.on('pointerdrag', onInteraction);
	view.on('change:resolution', onInteraction)

	setLayer(layers.length - 1);
	sendLayerNames();
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

	mapLink.layer_names(JSON.stringify(names));
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
