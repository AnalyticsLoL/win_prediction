import plotly.graph_objects as go

def linechart(data: dict[str], title: str, xaxis_title: str, yaxis_title: str, template: str ="plotly_white", yaxis: dict = None, **kwargs):
    """
    Create an interactive line chart using Plotly.
    This function creates a line chart with one or more traces using Plotly's go.Figure
    and go.Scatter objects. The primary data is passed as a dictionary, and additional
    traces can be added via keyword arguments.
    Parameters
    ----------
    data : dict[str]
        Dictionary containing the primary trace data with keys:
        - 'x': x-axis values
        - 'y': y-axis values
        - 'name' (optional): name for the trace (defaults to 'Data')
        - 'mode' (optional): plotting mode (defaults to 'lines')
    title : str
        Title of the chart
    xaxis_title : str
        Label for the x-axis
    yaxis_title : str
        Label for the y-axis
    template : str, optional
        Plotly template to use (default is 'plotly_white')
    **kwargs
        Additional trace data dictionaries to plot. Each dictionary should follow
        the same format as the primary 'data' parameter.
    Returns
    -------
    None
        The function displays the chart but does not return any value.
    Examples
    --------
    >>> linechart(
    ...     {'x': [1, 2, 3], 'y': [4, 5, 6], 'name': 'Series 1'},
    ...     title='Sample Chart',
    ...     xaxis_title='X Values',
    ...     yaxis_title='Y Values',
    ...     series2={'x': [1, 2, 3], 'y': [7, 8, 9], 'name': 'Series 2', 'mode': 'markers'}
    ... )
    """
    fig = go.Figure()
    
    def add_trace_data(trace_data):
        x = trace_data['x']
        y = trace_data['y']
        name = trace_data.get('name', 'Data')
        mode = trace_data.get('mode', 'lines')
        
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode=mode,
                name=name
            )
        )
    
    add_trace_data(data)
    
    for _, value in kwargs.items():
        if isinstance(value, dict):
            add_trace_data(value)
    
    fig.update_layout(
        title=title,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        template=template,
        showlegend=True,
        yaxis=yaxis,
        width=1000,
        height=500
    )
    
    fig.show()

def accuracy(train_acc, val_acc=None, title="Training and Validation Accuracy", xaxis_title="Epochs", yaxis_title="Accuracy"):
    train = {
        'x': list(range(1, len(train_acc) + 1)),
        'y': train_acc,
        'name': 'Train Accuracy'
    }
    
    if val_acc is not None:
        val = {
            'x': list(range(1, len(val_acc) + 1)),
            'y': val_acc,
            'name': 'Validation Accuracy'
        }
    else:
        val = None
    
    linechart(
        data=train,
        title=title,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        validation=val
    )

def loss(train_loss, val_loss=None, title="Training and Validation Loss", xaxis_title="Epochs", yaxis_title="Binary Cross Entropy Loss"):
    train = {
        'x': list(range(1, len(train_loss) + 1)),
        'y': train_loss,
        'name': 'Train Loss'
    }
    
    if val_loss is not None:
        val = {
            'x': list(range(1, len(val_loss) + 1)),
            'y': val_loss,
            'name': 'Validation Loss'
        }
    else:
        val = None
    
    linechart(
        data=train,
        title=title,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        validation=val
    )
    
def confusion_matrix(cm, title="Confusion Matrix", xaxis_title="Predicted Label", yaxis_title="True Label"):
    fig = go.Figure(data=go.Heatmap(
        z=cm,
        x=["Predicted Loss", "Predicted Win"],
        y=["True Loss", "True Win"],
        colorscale="Viridis",
        colorbar=dict(title="Count")
    ))

    fig.update_layout(
        title=title,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        xaxis=dict(tickmode='array', tickvals=[0, 1], ticktext=["Predicted Loss", "Predicted Win"]),
        yaxis=dict(tickmode='array', tickvals=[0, 1], ticktext=["True Loss", "True Win"]),
        template="plotly_white",
        width=350,
        height=350
    )

    fig.show()