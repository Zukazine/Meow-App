from django.shortcuts import render

# generic base view
from django.views.generic import TemplateView

# folium
import folium
from folium import plugins

# gee
import ee

# ee.Authenticate()
ee.Initialize(project='meow-project-401319')


# home
class home(TemplateView):
    template_name = 'firstfile.html'

    # Define a method for displaying Earth Engine image tiles on a folium map.
    def get_context_data(self, **kwargs):
        figure = folium.Figure()

        # create Folium Object
        m = folium.Map(
            location=[28.5973518, 83.54495724],
            zoom_start=8
        )

        # add map to figure
        m.add_to(figure)

        # select the Dataset Here's used the MODIS data
        dataset = (ee.ImageCollection('MODIS/006/MOD13Q1')
                   .filter(ee.Filter.date('2019-07-01', '2019-11-30'))
                   .first())
        modisndvi = dataset.select('NDVI')

        # Styling
        vis_paramsNDVI = {
            'min': 0,
            'max': 9000,
            'palette': ['FE8374', 'C0E5DE', '3A837C', '034B48', ]}

        # add the map to the the folium map
        map_id_dict = ee.Image(modisndvi).getMapId(vis_paramsNDVI)

        # GEE raster data to TileLayer
        folium.raster_layers.TileLayer(
            tiles=map_id_dict['tile_fetcher'].url_format,
            attr='Google Earth Engine',
            name='NDVI',
            overlay=True,
            control=True
        ).add_to(m)

        # add Layer control
        m.add_child(folium.LayerControl())

        # figure
        figure.render()

        # return map
        return {"map": figure}

def geospatial_view(request):
    # Authenticate to Earth Engine
    ee.Authenticate()
    ee.Initialize()

    # Define your region of interest (ROI) as a geometry
    roi = ee.Geometry.Polygon(
        [[[-180, -90], [-180, 90], [180, 90], [180, -90], [-180, -90]]]
    )

    # Create an image collection from Landsat images
    image_collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
        .filterBounds(roi) \
        .filterDate('2014-03-18', '2014-03-19')  # Adjust the date range as needed

    # Use the mosaic method to create a single image from the collection
    image = image_collection.mosaic()

    # Compute some operation on the merged image
    result = image.normalizedDifference(['B5', 'B4'])

    # Define the region for export
    export_region = roi

    # Export the result as an image to Google Drive
    task = ee.batch.Export.image.toDrive(
        image=result,
        description='NDVI_Merged',
        region=export_region,
        scale=30,  # Specify the scale of the output
    )
    task.start()

    # Get the task status and download link
    task_status = task.status()
    download_link = None

    if 'state' in task_status:
        if task_status['state'] == 'COMPLETED':
            download_link = task_status['output_url']

    context = {'map_url': download_link}
    return render(request, 'geospatial_template.html', context)