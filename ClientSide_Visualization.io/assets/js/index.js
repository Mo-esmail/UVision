let humArr = [], tempArr = [], upArr = [];
    const socket = new WebSocket('wss://okgt7rxrrl.execute-api.eu-west-2.amazonaws.com/production')
    
    socket.addEventListener('open', event => {
      console.log('WebSocket is connected, now check for your new Connection ID in Cloudwatch and the Parameter Store on AWS')
    })
    socket.addEventListener('message', event => {
        drawMainChart(event.data);  
        drawNumberOfvehiclesChart(event.data); 
        drawAverageSpeedChart(event.data);
    });

    let drawMainChart = function (data) {
  
        var IoT_Payload = JSON.parse(data)
        let { Average_Speed, No_Of_Cars, Timestamp } = IoT_Payload;
        var date = new Date(IoT_Payload.Timestamp);
        humArr.push(Number(IoT_Payload.Average_Speed));
        tempArr.push(Number(IoT_Payload.No_Of_Cars));
        upArr.push(date.getDate()+"/"+
        (date.getMonth()+1)+
        "/"+date.getFullYear()+
        " "+date.getHours()+
        ":"+date.getMinutes()+
        ":"+date.getSeconds());
        MainChart.series[0].setData(humArr , true)
        MainChart.series[1].setData(tempArr , true)
    }
    let drawNumberOfvehiclesChart = function (data){
        var IoT_Payload = JSON.parse(data);
        var newVal = (IoT_Payload.No_Of_Cars);
        point = NumberOfvehiclesChart.series[0].points[0];
        point.update(newVal);
    }
    let drawAverageSpeedChart = function (data){
        var IoT_Payload = JSON.parse(data);
        var newVal = (IoT_Payload.Average_Speed);
        point = AverageSpeedChart.series[0].points[0];
        point.update(newVal);
    }


    let MainChart = Highcharts.chart('container1', { 
        title: {
            text: 'Live chart'
        },
        
        data: {
            enablePolling: true,
            dataRefreshRate: 1
        },
    
        subtitle: {
            text: 'subtitle'
        },
    
        yAxis: {
            title: {
                text: 'Value'
            }
        },
    
        xAxis: {
            categories: upArr
        },
    
        legend: {
            layout: 'vertical',
            align: 'right',
            verticalAlign: 'middle'
        },
    
        plotOptions: {
            series: {
                label: {
                    connectorAllowed: false
                }
            }
        },
        series: [{
            name: 'Average Speed',
            data: []
        }, {
            name: 'Number of vehicles',
            data: []
        }],
    
        responsive: {
            rules: [{
                condition: {
                    maxWidth: 500
                },
                chartOptions: {
                    legend: {
                        layout: 'horizontal',
                        align: 'center',
                        verticalAlign: 'bottom'
                    }
                }
            }]
        }
    
    });

    var gaugeOptions = {
        chart: {
          type: 'solidgauge'
        },
      
        title: null,
      
        pane: {
          center: ['50%', '85%'],
          size: '140%',
          startAngle: -90,
          endAngle: 90,
          background: {
            backgroundColor:
              Highcharts.defaultOptions.legend.backgroundColor || '#EEE',
            innerRadius: '60%',
            outerRadius: '100%',
            shape: 'arc'
          }
        },
      
        exporting: {
          enabled: false
        },
      
        tooltip: {
          enabled: false
        },
      
        // the value axis
        yAxis: {
          stops: [
            [0.1, '#55BF3B'], // green
            [0.5, '#DDDF0D'], // yellow
            [0.9, '#DF5353'] // red
          ],
          lineWidth: 0,
          tickWidth: 0,
          minorTickInterval: null,
          tickAmount: 2,
          title: {
            y: -70
          },
          labels: {
            y: 16
          }
        },
      
        plotOptions: {
          solidgauge: {
            dataLabels: {
              y: 5,
              borderWidth: 0,
              useHTML: true
            }
          }
        }
    };

    var NumberOfvehiclesChart = Highcharts.chart('container2', Highcharts.merge(gaugeOptions, {
        title: {
            text: 'Number of vehicles'
        },
    yAxis: {
        
        min: 0,
        max: 200,
        title: {
        text: 'vehicle'
        }
    },

    credits: {
        enabled: false
    },

    series: [{
        name: 'vehicles',
        data: [0],
        dataLabels: {
        format:
            '<div style="text-align:center">' +
            '<span style="font-size:25px">{y}</span><br/>' +
            '<span style="font-size:12px;opacity:0.4">vehicle</span>' +
            '</div>'
        },
        tooltip: {
        valueSuffix: ' vehicle'
        }
    }]

    }));

    var AverageSpeedChart = Highcharts.chart('container3', Highcharts.merge(gaugeOptions, {
        title: {
            text: 'Average speed'
        },
    yAxis: {
        
        min: 0,
        max: 200,
        title: {
        text: 'Average speed'
        }
    },

    credits: {
        enabled: false
    },

    series: [{
        name: 'Average speed',
        data: [0],
        dataLabels: {
        format:
            '<div style="text-align:center">' +
            '<span style="font-size:25px">{y}</span><br/>' +
            '<span style="font-size:12px;opacity:0.4">km/h</span>' +
            '</div>'
        },
        tooltip: {
        valueSuffix: ' Km/h'
        }
    }]

    }));
   