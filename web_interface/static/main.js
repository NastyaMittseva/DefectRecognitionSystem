$(function() {
    // загружает изображения в карусель
    function get_carousel(imgs){
        var i = 0;
        $('#carouselContainer').html('');
        $.each(imgs, function (key, data) {
            var value = '';
            if(i == 0){
              value =
                  `<div class="carousel-item active">
                    <img src="${data.path_to_image}" class="d-block carousel-image" alt="Изображения">
                    </div>
                  `;
            }
            else {
              value =
                `<div class="carousel-item">
                  <img src="${data.path_to_image}" class="d-block carousel-image" alt="Изображения">
                  </div>
                `;
            }
            $('#carouselContainer').append(value);
            i += 1;
        });
        $('.carousel-control-prev').removeAttr('hidden');
        $('.carousel-control-next').removeAttr('hidden');
    }

    // загружает строки в таблицу
    function get_table(data){
        for (var arr in data){
            var row_data = [];
            var obj = data[arr];
            row_data.push(obj['id']);
            row_data.push(obj['image_name']);
            row_data.push(obj['action']);
            row_data.push(obj['result']);
            row_data.push(obj['time']);
            $('#current_results').dataTable().fnAddData(row_data);
        }
    }

    // подгружает исходное состояние
    function get_state(){
        var imgs = JSON.parse(localStorage.getItem('carousel'));
        if (imgs){
            get_carousel(imgs);
        }
        var table = $('#current_results').dataTable();
        var data = JSON.parse(localStorage.getItem('table'));
        for (var ind in data){
            row_data = []
            for (var val in data[ind]){
                row_data.push(data[ind][val]);
            }
            table.fnAddData(row_data);
        }
    }
    get_state();


  // загрузка изображений
  $('body').on('change', '#upload_image', function(){
    $("#spinner").removeAttr("hidden");
    $('#carouselExampleControls').attr('hidden', 'hidden');
    var form_data = new FormData();
    var ins = document.getElementById('upload_image').files.length;
    for (var x = 0; x < ins; x++)
      form_data.append("files[]", document.getElementById('upload_image').files[x]);
//
//    for (var value of form_data.values()) {
//           console.log(value);
//    }

    $.ajax({
      url: '/images',
      dataType: 'json',
      cache: false,
      contentType: false,
      processData: false,
      data: form_data,
      type: 'post',
      success: function (response) {
        if (response['message'] === undefined){
            $('#spinner').attr('hidden', 'hidden');
            $("#carouselExampleControls").removeAttr("hidden");
            get_carousel(response['imgs']);
            $('#upload_image').val('');
            var dataToStore = JSON.stringify(response['imgs']);
            localStorage.setItem('carousel', dataToStore);
        }
        else {
            alert(response['message']);
        }
      }
    });
  });
  
    
  // загрузка тестовых изображений
  $('body').on('click', '#load_test', function(){
    $("#spinner").removeAttr("hidden");
    $('#carouselExampleControls').attr('hidden', 'hidden');
    $.ajax({
      url: '/test_images',
      dataType: 'json',
      cache: false,
      contentType: false,
      processData: false,
      data: false,
      type: 'post',
      success: function (response) {
        if (response['message'] === undefined){
            $('#spinner').attr('hidden', 'hidden');
            $("#carouselExampleControls").removeAttr("hidden");
            get_carousel(response['imgs']);
            $('#upload_image').val('');
            var dataToStore = JSON.stringify(response['imgs']);
            localStorage.setItem('carousel', dataToStore);
        }
        else {
            alert(response['message']);
        }
      }
    });
  });
    
  // распознавание шва
  $('body').on('click', '#recognize_weld', function(){
    var form_data = new FormData();
    $.each($('#carouselContainer .carousel-item .d-block'), function (key, data) {
        form_data.append("img_paths[]",$(data).attr('src'));
    });

    if ($('#carouselContainer .carousel-item').length < 1) {
        alert("Load images!");
        return false;
    }
    $.ajax({
      url: '/welds',
      dataType: 'json',
      cache: false,
      contentType: false,
      processData: false,
      data: form_data,
      type: 'post',
      success: function (response) {
        get_table(response['results']);
        var table = $('#current_results').DataTable();
        localStorage.setItem('table', JSON.stringify(table.rows().data().toArray()));
      }
    });
  });

  // распознавание дефектов
  $('body').on('click', '#recognize_defects', function(){
    var form_data = new FormData();
    $.each($('#carouselContainer .carousel-item .d-block'), function (key, data) {
        form_data.append("img_paths[]",$(data).attr('src'));
    });

    if ($('#carouselContainer .carousel-item').length < 1) {
        alert("Load images!");
        return false;
    }
    $.ajax({
      url: '/defects',
      dataType: 'json',
      cache: false,
      contentType: false,
      processData: false,
      data: form_data,
      type: 'post',
      success: function (response) {
        get_table(response['results']);
        var table = $('#current_results').DataTable();
        localStorage.setItem('table', JSON.stringify(table.rows().data().toArray()));
      }
    });
  });

  // классификация дефектов
  $('body').on('click', '#classify_defects', function(){
    var form_data = new FormData();
    $.each($('#carouselContainer .carousel-item .d-block'), function (key, data) {
        form_data.append("img_paths[]",$(data).attr('src'));
    });

    if ($('#carouselContainer .carousel-item').length < 1) {
        alert("Load images!");
        return false;
    }
    $.ajax({
      url: '/defects_by_class',
      dataType: 'json',
      cache: false,
      contentType: false,
      processData: false,
      data: form_data,
      type: 'post',
      success: function (response) {
        get_table(response['results']);
        var table = $('#current_results').DataTable();
        localStorage.setItem('table', JSON.stringify(table.rows().data().toArray()));
      }
    });
  });

  // скрытие результатов
  $('#hide_images').click( function () {
    $('#gridContainer').html('');
    var table = $('#current_results').DataTable();
    table.$('tr.selected').removeClass('selected');
  } );

  $(document).ready(function() {
    // инициализация таблицы с текущими результатами
    var table = $('#current_results').DataTable( {
        pageLength : 5,
        lengthMenu: [[5, 10, 20, -1], [5, 10, 20, 'Todos']],
        "columns": [
                    { "width": "25%" },
                    { "width": "25%" },
                    { "width": "20%" },
                    { "width": "25%" },
                    { "width": "5%" }
                  ],
        stateSave: true,
        "bDestroy": true
    } )

    // инициализация таблицы с историей
    var history_table = $('#history_results').DataTable( {
        pageLength : 10,
        lengthMenu: [[5, 10, 20, -1], [5, 10, 20, 'Todos']],
        stateSave: true
    } )

    $('#current_results tbody').on( 'click', 'tr', function () {
        $(this).toggleClass('selected');
    } );

    // отображение результатов в виде картинок
    $('#show_images').click( function () {
        var form_data = new FormData();
        for (var i = 0; i < table.rows('.selected').data().length; ++i) {
            form_data.append("rows[]",table.rows('.selected').data()[i]);
        }

        $.ajax({
          url: '/results_as_images',
          dataType: 'json',
          cache: false,
          contentType: false,
          processData: false,
          data: form_data,
          type: 'post',
          success: function (response) {
            $('#gridContainer').html('');
            if (response['results'] != '' && response['results'] != 'undefined' && response['results'] != 'none'){
                 var value = '<br><br><table><thead><tr><th colspan="2" style="text-align:center; color:#000000; font-size:20px">Recognition results</th></tr>';
                 value += '<tr><th style="text-align:center">Original shot</th><th style="text-align:center">Result</th></tr></thead>'
            }
            else{
                alert('Results are not selected!')
            }

            $.each(response['results'], function (key, data) {
                value += '<tr>';
                value += `<td><img src="${data['path_to_image']}" class="grid-image" alt="Изображения"></td>`;
                value += `<td><img src="${data['path_to_result']}" class="grid-image" alt="Изображения"></td>`;
                value += '</tr>';
                value += `<tr><td colspan="2">Description: ${data['description']}</td></tr>`;

            });
            value += '</table>';
            $('#gridContainer').append(value);
          }
        });
    } );

    // очистка таблицы
    $('#clear_table').click( function () {
        $('#current_results').dataTable().fnClearTable();
        var table = $('#current_results').DataTable();
        localStorage.setItem('table', JSON.stringify(table.rows().data().toArray()));
    } );
   });

   $('#logout').on('click', function() {
        localStorage.clear();
	});

});

