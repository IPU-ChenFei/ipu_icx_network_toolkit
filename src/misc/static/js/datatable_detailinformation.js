

$(document).ready(function() {



    $('#example').DataTable( {
        dom: 'Bfrtip',
        "pageLength": 50,
        buttons: [
            'copy', 'csv', 'excel', 'pdf', 'print', 'columnsToggle'

        ],

        initComplete: function () {
            this.api().columns().every( function () {
                var column = this;
                var select = $('<select><option value=""></option></select>')
                    .appendTo( $(column.footer()).empty() )
                    .on( 'change', function () {
                        var val = $.fn.dataTable.util.escapeRegex(
                            $(this).val()
                        );

                        if (val === "")
                            column
                                .search('^$', true, false)
                                .draw();
                        else
                            column
                                   .search( val ? '^'+val+'$' : '', true, false )
                                   .draw();
                    } );

                column.data().unique().sort().each( function ( d, j ) {
                    select.append( '<option value="'+d+'">'+d+'</option>' )
                } );
            } );
        }

    } );
} );