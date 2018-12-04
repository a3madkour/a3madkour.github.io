function glyph_statechart(id, maxWidth, maxHeight, left, top){
    // 1. Set up the div to store the chart
    
    this.margin = {top: 20, right: 20, bottom: 40, left: 50};
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

glyph_statechart.prototype = {
    init: function(data, stateMap, fill){
        this.data = data;
        this.stateMap = stateMap;
        this.fill = fill;
        
        // currently trajectory contains only states
        maxX = _.max(_.map(this.data.trajectories, function(d){ return d.trajectory.length;}));
//        console.log(maxX);
        
        // 3. Set up the coordinate system
        this.x = d3.scale.linear()
            .domain([0,maxX])
            .range([0, this.width]);
        // x domain will be updated according to the length of the sequences

        this.y = d3.scale.linear()
            .domain([-15,75])
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
            .attr("transform", "translate(0," + this.height + ")")
            .call(this.xAxis);

        this.trajSVG.append("text")      // text label for the x axis
            .attr("x", this.width )
            .attr("y", this.height+this.margin.bottom-5)
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
            .text("Marker Position");

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
            .text("State Chart");

        // CONSTRUCT line from data
        var chartObject = this; 
        this.valueline= d3.svg.line()
            .x(function(d){return chartObject.x(d.t);})
            .y(function(d){return chartObject.y(d.pos);});

    },
    
    // traj is a trajectory object
    // return only the state (even indices)
    getStateIDs: function(traj){
//        console.log(traj);
        return traj;
    },
    
    
    detailsArray: ["ESP.Analytics.InfantryMountEvent",
             "ESP.Analytics.DestroyedEvent",
             "DRE",
             "WD",
             "ESP.Analytics.UseOpticEvent"],
    
    // details is a string representing the action
    // the returned value is scattered with interval
    // 15 across the y-axis
    detailsToInt: function(details){
        return 15 * _.indexOf(this.detailsArray, details);
    },
    // selectedBehaviorNodes is an array of integer indices
    // of behavior nodes
    generateTrajPopup: function(selectedBehaviorNodes, color){

//        console.log(this.getStateIDs(this.data.trajectories[selectedBehaviorNodes[0]].trajectory));
//        console.log(this);
            
        var allLines = _.map(selectedBehaviorNodes, function(aBNode, ind){
//            console.log(this);
            stateIDs = this.getStateIDs(this.data.trajectories[aBNode].trajectory);    
            positions = _.map(stateIDs, function(stateId, index){
                return this.detailsToInt(this.stateMap[stateId].details);
            }, this); 
            return {bID: aBNode, traj: _.map(positions, function(pos, ind){return {'pos': pos, 't':ind};})};
        }, this); // "this" is the context, i.e. the object referred to as "this" in the codes

        this.drawLines(allLines, color);
    },
    
    
    // if color is set, all lines will have that color
    drawLines: function(allLines, color){
    //            console.log(coordinates);
//        console.log(this.valueline);
        var chartObject = this;
        
        var drewLines = chartObject.trajSVG.selectAll("g.behavior-line")
            .data(allLines);

        drewLines.exit().remove();
        var lineGroup = drewLines.enter().append("g").attr("class", "behavior-line");


        // Enter: line: Non-nesting
        lineGroup.append('path')
            .attr("class", "line")
            .style('stroke', function(d, i){ 
                if (color === undefined)
                    return chartObject.fill(i);
                else return color;
            })
            .attr("d", function(d){ 
                return chartObject.valueline(d.traj);
            });
        
        lineGroup.append("text")
            .attr("transform", function(d, i) { return "translate(" + chartObject.x(d.traj.length-1) + "," + chartObject.y(d.traj[d.traj.length-1].pos) + ")"; })
            .attr("x", 3)
            .attr("dy", ".35em")
            .attr('fill', function(d, i){
                if (color === undefined)
                    return chartObject.fill(i);
                else return color;                
            })
            .text(function(d) { return d.bID; });


        // update
        drewLines.select('path.line')
            .style('stroke', function(d, i){ 
                if (color === undefined)
                    return chartObject.fill(i);
                else return color;
            })
            .attr("d", function(d){ return chartObject.valueline(d.traj);});
        
        drewLines.select('text')
            .attr("transform", function(d, i) { return "translate(" + chartObject.x(d.traj.length-1) + "," + chartObject.y(d.traj[d.traj.length-1].pos) + ")"; })
            .attr("x", 3)
            .attr("dy", ".35em")
            .attr('fill', function(d, i){
                if (color === undefined)
                    return chartObject.fill(i);
                else return color;                
            })
            .text(function(d) { return d.bID; });
        
        // Nested entering: Need to return d, as the data to be used
        // for this enter
        var drewDots = drewLines.selectAll("circle")
            .data(function(d,i){return d.traj;});

        drewDots.enter().append("circle")
            .attr("r", 3.5)
            .attr("cx", function(d) { return chartObject.x(d.t); })
            .attr("cy", function(d) { return chartObject.y(d.pos); });

        drewDots.exit().remove();

        drewDots.attr("r", 3.5)
            .attr("cx", function(d) { return chartObject.x(d.t); })
            .attr("cy", function(d) { return chartObject.y(d.pos); });    
    }
};
