function glyph_actionchart(id, maxWidth, maxHeight, left, top){
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

    // 2. set up the SVG with coordinates
    this.trajSVG = this.trajComparisonPopup.append("svg")
                    .attr("width", this.width + this.margin.left + this.margin.right)
                    .attr("height", this.height + this.margin.top + this.margin.bottom)
                .append("g")
                    .attr("transform", "translate(" + this.margin.left + "," + this.margin.top + ")");
}

Array.prototype.subarray=function(start,end){
     if(!end){ end=-1;} 
    return this.slice(start, this.length+1-(end*-1));
};

glyph_actionchart.prototype = {
    init: function(data, actionMap, fill){
        this.data = data;
        this.actionMap = actionMap;
        this.fill = fill;

        // 3. Set up the coordinate system
        
        maxX = _.max(_.map(this.data.trajectories, function(d){ return d.trajectory.length;}));
//        console.log(maxX);
        
        this.x = d3.scale.linear()
            .domain([0,maxX])
            .range([0, this.width]);
        // x domain will be updated according to the length of the sequences

        maxNumTeeth = _.max(this.data.level_info.gears);
        this.y = d3.scale.linear()
            .domain([-maxNumTeeth*5,maxNumTeeth*5])
            .range([this.height, 0]);


        this.xAxis = d3.svg.axis()
            .scale(this.x)
            .orient("bottom")
            .ticks(20); // define the major ticks on the axes

        this.yAxis = d3.svg.axis()
            .scale(this.y)
            .orient("left");
    //            .ticks(5);

        this.trajSVG.append("g")			// Add the X Axis
            .attr("class", "x axis")
            .attr("transform", "translate(0," + this.height/2 + ")")
            .call(this.xAxis);
        this.trajSVG.selectAll(".x text")
            .attr("transform", "translate(-6, -2)"); 

        this.trajSVG.append("text")      // text label for the x axis
            .attr("x", this.width )
            .attr("y", this.height/2+this.margin.bottom)
            .style("text-anchor", "end")
            .text("Time step");        

        this.trajSVG.append("g")			// Add the Y Axis
            .attr("class", "y axis")
            .call(this.yAxis);
        
        this.trajSVG.append("text")         // text label for the y axis
            .attr("transform", "rotate(-90)")
            .attr("x", -this.height/2 )
            .attr("y", -this.margin.left)
            .attr("dy", "1em")
            .style("text-anchor", "middle")
            .text("Wheel Displacement");

        this.trajSVG.append("g")			
            .attr("class", "grid")
            .attr("transform", "translate(0," + this.height + ")")
            .call(this.xAxis
                .tickSize(-this.height, 0, 0)
                .tickFormat("")
            );

        this.trajSVG.append("g")			
            .attr("class", "grid")
            .call(this.yAxis
                .tickSize(-this.width, 0, 0)
                .tickFormat("")
            );
        
        this.trajSVG.append("text")
            .attr("x", this.width)             
            .attr("y", this.margin.top)
            .attr("text-anchor", "end")  
            .style("font-size", "20px")
            .style("font-weight", "bold")
//            .style("text-decoration", "underline")  
            .text("Action Chart");

        // CONSTRUCT line from data
        var chartObject = this; 
        this.valueline= d3.svg.line()
            .x(function(d){return chartObject.x(d.t);})
            .y(function(d){return chartObject.y(d.move);});
    },
    
    
    // traj is a trajectory object
    // return only the state (even indices)
    getActionIDs: function(traj){
        
        if (traj.length > 1){
        
            orig = traj.subarray(0,-2);
            target = traj.subarray(1);
            return _.map(orig, function(o, i){return [o, target[i]].join('_')});    
        }
        return [];
    },
    
    // selectedBehaviorNodes is an array of integer indices
    // of behavior nodes
    generateTrajPopup: function(selectedBehaviorNodes, color){

        allLines = _.map(selectedBehaviorNodes, function(aBNode, ind){
            actionIDs = this.getActionIDs(this.data.trajectories[aBNode].trajectory);    
            
            moves = _.map(actionIDs, function(actionId, index){
                return this.actionMap[actionId].num_moves;
            }); 
            
            return _.map(moves, function(move, i){return {'move': move, 't':i, 'line_index': ind};});
        }, this);

//        console.log(allLines);
        this.drawLines(allLines, color);
    },
    
    // if color is set, all lines will have that color
    drawLines: function(allLines, color){
    //            console.log(coordinates);
//        console.log(this.valueline);
        var chartObject = this;
        
        var drewLines = chartObject.trajSVG.selectAll("g.action-line")
            .data(allLines);

        drewLines.exit().remove();
        var lineGroup = drewLines.enter().append("g").attr("class", "action-line");

        // line: Non-nesting
        var lineObject = lineGroup.append('path')
            .attr("class", "line")
            .style('stroke', function(d, i){ 
                if (color === undefined)
                    return chartObject.fill(i);
                else return color;
            })
            .attr("d", function(d){ 
                return chartObject.valueline(d);
            });

        // update
        drewLines.select('path.line')
            .style('stroke', function(d, i){ 
                if (color === undefined)
                    return chartObject.fill(i);
                else return color;
            })
            .attr("d", function(d){ return chartObject.valueline(d);});


        // Nested entering: Need to return d, as the data to be used
        // for this enter
        var drewSegments = drewLines.selectAll("rect")
            .data(function(d,i){
                return d;
            });

        drewSegments.enter().append("rect")
            .style("fill", function(d, i){
//                console.log(d);
                if (color === undefined)
                    return chartObject.fill(d.line_index);
                else return color;
            })
              .attr("x", function(d) { return chartObject.x(d.t);})
              .attr("width", 10)
              .attr("y", function(d) { return chartObject.y(d.move)-2*d.line_index; })
              .attr("height", 5);

        drewSegments.exit().remove();

        drewSegments.style("fill", function(d, i){
//            console.log(d);
                if (color === undefined)
                    return chartObject.fill(d.line_index);
                else return color;
            })
              .attr("x", function(d) { return chartObject.x(d.t);})
              .attr("width", 10)
              .attr("y", function(d) { return chartObject.y(d.move)-2*d.line_index; })
              .attr("height", function(d) { return 5});
    }
};
