$("#id_username").autocomplete({
    source: function(request, response){
        $.ajax({
            url: "{% url autocomplete 'user' %}",
            data: {q: request.term},
            success: function(data) {
                response($.map(data, function(item) {
                    return {
                        label: item[1],
                        value: item[1]
                    };
                }));
            },
            dataType: "json"
        });
    },
    minLength: 2
});


$("#id_authenticated_username").autocomplete({
    source: function(request, response){
        $.ajax({
            url: "{% url authenticated_autocomplete 'user' %}",
            data: {q: request.term},
            success: function(data) {
                response($.map(data, function(item) {
                    return {
                        label: item.first_name + " " + item.last_name + " <" + item.email + ">",
                        value: item.username
                    };
                }));
            },
            dataType: "json"
        });
    },
    minLength: 2
});


$("#id_standalone_username").autocomplete({
    source: function(request, response){
        $.ajax({
            url: "{% url autocomplete 'user'%}",
            data: {q: request.term},
            success: function(data) {
                response($.map(data, function(item) {
                    return {
                        label: item[1],
                        value: item[1]
                    };
                }));
            },
            dataType: "json"
        });
    },
    minLength: 2
});
