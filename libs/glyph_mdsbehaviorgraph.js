function glyph_mdsbehaviorgraph(id, maxWidth, maxHeight, left, top){
    // 1. Set up the div to store the chart
    
    this.margin = {top: 20, right: 20, bottom: 30, left: 50};
    this.width = maxWidth - this.margin.left - this.margin.right;
    this.height = maxHeight - this.margin.top - this.margin.bottom;

    this.trajComparisonPopup = d3.select("body").append("div")
        .attr("class", "popup")
        .attr("id", id)
        .style("width", maxWidth.toString() + 'px')
        .style("height", maxHeight.toString() + 'px')
        .style("left", left.toString() + 'px')
        .style("top", top.toString() + 'px')
        .style("opacity", 1.0);

//    // 2. set up the SVG with coordinates
//    this.trajSVG = this.trajComparisonPopup.append("svg")
//                    .attr("width", maxWidth)
//                    .attr("height", maxHeight)
//                .append("g")
//                    .attr("transform", "translate(" + this.margin.left + "," + this.margin.top + ")");
}

glyph_mdsbehaviorgraph.prototype = {
    
    init: function(data){
        
//        // 3. Set up the coordinate system
//        this.x = d3.scale.linear()
//            .domain([0,20])
//            .range([0, this.width]);
//        // x domain will be updated according to the length of the sequences
//
//        this.y = d3.scale.linear()
//            .domain([0, 20])
//            .range([this.height, 0]);
//
//        this.xAxis = d3.svg.axis()
//            .scale(this.x)
//            .orient("bottom");
////            .ticks(20); // define the major ticks on the axes
//
//        this.yAxis = d3.svg.axis()
//            .scale(this.y)
//            .orient("left");
//    //            .ticks(5);
//
//        this.trajSVG.append("g")			// Add the X Axis
//            .attr("class", "x axis")
//            .attr("transform", "translate(0," + this.height + ")")
//            .call(this.xAxis);
//
//        this.trajSVG.append("text")      // text label for the x axis
//            .attr("x", this.width )
//            .attr("y", this.height+this.margin.bottom-5)
//            .style("text-anchor", "end")
//            .text("Time step");
//        
//        this.trajSVG.append("g")			// Add the Y Axis
//            .attr("class", "y axis")
//            .call(this.yAxis);
//                
//        this.trajSVG.append("text")         // text label for the y axis
//            .attr("transform", "rotate(-90)")
//            .attr("x", -this.height/2 )
//            .attr("y", -this.margin.left)
//            .attr("dy", "1em")
//            .style("text-anchor", "middle")
//            .text("Wheel Displacement");
//
//        // grid
//        this.trajSVG.append("g")			
//            .attr("class", "grid")
//            .attr("transform", "translate(0," + this.height + ")")
//            .call(this.xAxis
//                .tickSize(-this.height, 0, 0)
//                .tickFormat("")
//            );
//
//        this.trajSVG.append("g")			
//            .attr("class", "grid")
//            .call(this.yAxis
//                .tickSize(-this.width, 0, 0)
//                .tickFormat("")
//            );
//        
        // title
//        this.trajSVG.append("text")
//            .attr("x", this.width)             
//            .attr("y", this.margin.top)
//            .attr("text-anchor", "end")  
//            .style("font-size", "20px")
//            .style("font-weight", "bold")
////            .style("text-decoration", "underline")  
//            .text("MDS");
        
        
        // compile the distance matrix
        this.data = data;
        matDim = data.trajectories.length;
        console.log("dim = " + matDim);
        distanceMatrix = new Array(matDim)
        _.each(_.range(matDim), function(d){
            distanceMatrix[d] = new Array(matDim);
            distanceMatrix[d][d] = 0;
        });
        
        _.each(data.traj_similarity, function(d){
            distanceMatrix[d.source][d.target] = distanceMatrix[d.target][d.source] = d.similarity;
        });
        
        console.log(JSON.stringify(distanceMatrix));
        
        nodePositions = numeric.transpose(mds.classic(distanceMatrix));
        
        // draw
        mds.drawD3ScatterPlot(this.trajComparisonPopup, 
                             nodePositions[0],
                             nodePositions[1],
                             _.range(matDim), // labels
                             {
            w: this.width,
            h: this.height,
            padding: 37,
            reverseX: true,
            reverseY:true,
        });
        
//        // CONSTRUCT line from data
//        var chartObject = this; 
//        this.valueline= d3.svg.line()
//            .x(function(d){return chartObject.x(d.t);})
//            .y(function(d){return chartObject.y(d.move);});
    },
        
    // draw the graph using MDS
    drawGraph: function(){
    
        // store this object to avoid overriden attribute this
        var chartObject = this;
        
        
        
//        var drewLines = chartObject.trajSVG.selectAll("g.action-line")
//            .data(allLines);
//
//        drewLines.exit().remove();
//        var lineGroup = drewLines.enter().append("g").attr("class", "action-line");
//
//        // line: Non-nesting
//        var lineObject = lineGroup.append('path')
//            .attr("class", "line")
//            .style('stroke', function(d, i){ 
//                if (color === undefined)
//                    return chartObject.fill(i);
//                else return color;
//            })
//            .attr("d", function(d){ 
//                return chartObject.valueline(d);
//            });
//
//        // update
//        drewLines.select('path.line')
//            .style('stroke', function(d, i){ 
//                if (color === undefined)
//                    return chartObject.fill(i);
//                else return color;
//            })
//            .attr("d", function(d){ return chartObject.valueline(d);});
//
//
//        // Nested entering: Need to return d, as the data to be used
//        // for this enter
//        var drewSegments = drewLines.selectAll("rect")
//            .data(function(d,i){
//                return d;
//            });
//
//        drewSegments.enter().append("rect")
//            .style("fill", function(d, i){
////                console.log(d);
//                if (color === undefined)
//                    return chartObject.fill(d.line_index);
//                else return color;
//            })
//              .attr("x", function(d) { return chartObject.x(d.t);})
//              .attr("width", 10)
//              .attr("y", function(d) { return chartObject.y(d.move)-2*d.line_index; })
//              .attr("height", 5);
//
//        drewSegments.exit().remove();
//
//        drewSegments.style("fill", function(d, i){
////            console.log(d);
//                if (color === undefined)
//                    return chartObject.fill(d.line_index);
//                else return color;
//            })
//              .attr("x", function(d) { return chartObject.x(d.t);})
//              .attr("width", 10)
//              .attr("y", function(d) { return chartObject.y(d.move)-2*d.line_index; })
//              .attr("height", function(d) { return 5});
    }
};
