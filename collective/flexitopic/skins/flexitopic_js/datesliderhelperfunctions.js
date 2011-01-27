var datesliderhelper  = {
    format_date: function (adate){
            var y = adate.getFullYear();
            var m = adate.getMonth() + 1;
            var d = adate.getDate();
            return ( ''+ y + '/' + m + '/' + d);
    },
    add_date: function(adate, days){
            var day = 1000*60*60*24;
            var new_date = new Date(adate.getTime() + (days * day));
            return new_date;
    }
};
