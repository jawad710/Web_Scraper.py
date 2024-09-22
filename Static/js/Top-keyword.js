am5.ready(function() {
    // Create root for Word Cloud chart
    var root = am5.Root.new("wordCloudChart");

    // Create Word Cloud chart
    var wordCloudChart = root.container.children.push(am5.WordCloud.new(root, {}));
    var wordCloudSeries = wordCloudChart.series.push(am5.WordCloudSeries.new(root, {
        valueField: "count",
        categoryField: "_id"
    }));

    // Fetch data for Word Cloud
    fetch('http://127.0.0.1:5000/top_keywords')
        .then(response => response.json())
        .then(data => {
            const filteredData = data.filter(item => item._id);  // Filter out invalid entries
            wordCloudSeries.data.setAll(filteredData);
        });

    wordCloudSeries.appear(1);
    wordCloudChart.appear(10, 1);

    // Create root for Bar Chart
    var barChartRoot = am5.Root.new("barChart");

    // Create XY (Bar) Chart
    var barChart = barChartRoot.container.children.push(am5xy.XYChart.new(barChartRoot, {}));

    // Define X-axis
    var xAxis = barChart.xAxes.push(am5xy.CategoryAxis.new(barChartRoot, {
        categoryField: "_id",
        renderer: am5xy.AxisRendererX.new(barChartRoot, {})
    }));

    // Define Y-axis
    var yAxis = barChart.yAxes.push(am5xy.ValueAxis.new(barChartRoot, {
        renderer: am5xy.AxisRendererY.new(barChartRoot, {})
    }));

    // Create Bar Series
    var barSeries = barChart.series.push(am5xy.ColumnSeries.new(barChartRoot, {
        valueYField: "count",
        categoryXField: "_id"
    }));

    // Fetch data for Bar Chart
    fetch('http://127.0.0.1:5000/top_keywords')
    .then(response => response.json())  // Convert response to JSON
    .then(data => {
        // Use all the data without filtering
        xAxis.data.setAll(data);  // Set the data for the X-axis
        barSeries.data.setAll(data);  // Set the data for the bar chart
    });

    barSeries.appear(1000);
    barChart.appear(1000, 100);
});
