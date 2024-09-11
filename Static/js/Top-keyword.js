am5.ready(function() {
    var root = am5.Root.new("chartdiv");

    var chart = root.container.children.push(am5xy.XYChart.new(root, {}));

    var xAxis = chart.xAxes.push(am5xy.CategoryAxis.new(root, {
        categoryField: "_id",
        renderer: am5xy.AxisRendererX.new(root, {})
    }));

    var yAxis = chart.yAxes.push(am5xy.ValueAxis.new(root, {
        renderer: am5xy.AxisRendererY.new(root, {})
    }));

    var series = chart.series.push(am5xy.ColumnSeries.new(root, {
        valueYField: "count",
        categoryXField: "_id"
    }));

    fetch('/api/top_keywords')
        .then(response => response.json())
        .then(data => {
            xAxis.data.setAll(data);
            series.data.setAll(data);
        });

    series.appear(1000);
    chart.appear(1000, 100);
});
