'use strict';

var server = 'http://localhost:19048';

function HomeCtrl($scope) {
}

function ExtremeDRCtrl($scope, $http){
   delete $http.defaults.headers.common['X-Requested-With'];

   $scope.panes = [{}];
   $scope.loaded = false;

   $http.get(server+'/json/extreme-dr').success(function (data) {
      $scope.loaded = true;
      $scope.highest = data.highest;
      $scope.lowest = data.lowest;
   });


}

function GetStartedCtrl($scope){
   $scope.panes = [{}];
}

function WavePlotUUIDCtrl($scope, $routeParams, $http){
   delete $http.defaults.headers.common['X-Requested-With'];

   $scope.uuid = $routeParams.uuid;
   $scope.element = { "data":"" };
   $scope.data = { "release":{"mbid":""} };
   $http.get(server+'/json/waveplot/'+$scope.uuid).success(function (data) {
      if(data.result == "success"){
         $scope.data = data.waveplot;

         $scope.data.source_type = $scope.data.source_type.toUpperCase();

         if($scope.data.source_type == "FLAC" && $scope.data.bit_rate == 0){
             $scope.data.bit_rate = "N/A";
         }

         $scope.element = {
            "uuid":$scope.uuid,
            "data":$scope.data.preview
         };
      } else {
         //Todo - deal with this.
         $scope.data = "Blob."
      }
   });
}

function WavePlotListCtrl($scope, $routeParams, $location, $http){
   delete $http.defaults.headers.common['X-Requested-With'];

  $scope.loaded = false;
    $scope.page = 1;

    $scope.displayWavePlot = function (uuid) {
        $location.path("/waveplot/"+uuid);
    };

    $scope.$watch('page', function(val) {
        if(val > 0) {
      $scope.loaded = false;
      $scope.listelements = undefined;

            $http.get(server+'/json/waveplot/list?page='+val).success(function (data) {
            $scope.listelements = data;
            $scope.valid_results = $scope.listelements.length;

            for(var i = 0; i != $scope.listelements.length; i++){
               if($scope.listelements[i].title == null) {
                  $scope.listelements[i].title = "<"+$scope.listelements[i].uuid+">";
                  $scope.listelements[i].style = { 'font-family': '"Courier New", Courier, monospace' }
               }
              if($scope.listelements[i].artist == null) {
                  $scope.listelements[i].artist = "<uncached>";
               }

              $scope.listelements[i].valid = true;
            }


            while($scope.listelements.length < 20){
               $scope.listelements.push({
                  "uuid":"",
                  "title":"",
                  "artist":"",
                  "data":"",
                  "valid":false });
               }

             $scope.loaded = true;
         });
        } else {
            $scope.page = 1;
        }
    },true);
}

function RecordingMBIDCtrl($scope,$routeParams,$location,$http){
   delete $http.defaults.headers.common['X-Requested-With'];

   $scope.mbid = $routeParams.mbid;

    $scope.page = 1;

    $scope.displayWavePlot = function (uuid) {
        $location.path("/waveplot/"+uuid);
    };

   $scope.$watch('page', function(val) {
        if(val > 0) {
            $http.get(server+'/json/waveplot/list?page='+val+'&recording='+$scope.mbid).success(function (data) {
            $scope.listelements = data;
            $scope.valid_results = $scope.listelements.length;

            for(var i = 0; i != $scope.listelements.length; i++){
               if($scope.listelements[i].title == null) {
                  $scope.listelements[i].title = "<"+$scope.listelements[i].uuid+">";
                  $scope.listelements[i].style = { 'font-family': '"Courier New", Courier, monospace' }
               }
              if($scope.listelements[i].artist == null) {
                  $scope.listelements[i].artist = "<uncached>";
               }

              $scope.listelements[i].valid = true;
            }


            while($scope.listelements.length < 20){
               $scope.listelements.push({
                  "uuid":"",
                  "title":"",
                  "artist":"",
                  "data":"",
                  "valid":false });
               }
         });
        } else {
            $scope.page = 1;
        }
    },true);
}

function RecordingListCtrl($scope,$location,$http){
   delete $http.defaults.headers.common['X-Requested-With'];

   $scope.num_links = 2;
   $scope.page = 1;
   $scope.loaded = false;

   $scope.displayRecording = function (mbid) {
        $location.path("/recording/"+mbid);
    };

   $scope.$watch('page', function(val) {
        if(val > 0) {
      $scope.listelements = undefined;
      $scope.loaded = false;
            $http.get(server+'/json/recording/list?linked-waveplots='+$scope.num_links+'&page='+val).success(function (data) {
            $scope.listelements = data;
          $scope.loaded = true;
         });
        } else {
            $scope.page = 1;
        }
    },true);

    $scope.$watch('num_links', function(val) {
    $scope.listelements = undefined;
    $scope.loaded = false;
        $http.get(server+'/json/recording/list?linked-waveplots='+val+'&page='+$scope.page).success(function (data) {
            $scope.listelements = data;
        $scope.loaded = true;
      });
      $scope.page = 1;
    },true);
}

function RegisterCtrl($scope,$http){
   delete $http.defaults.headers.common['X-Requested-With'];
   $http.defaults.headers.post["Content-Type"] = "application/x-www-form-urlencoded";

   $scope.input_error = false;
   $scope.email = "";
   $scope.submitted = false;

   $scope.submit = function(){
      if ((typeof $scope.email == 'undefined') || ($scope.email == '')) {
         $scope.input_error = true;
      } else {
         $scope.input_error = false;
         $http.post(server+'/json/editor',"username="+$scope.username+"&email="+$scope.email).success(function(data) {
            $scope.submitted = true;
            if(data.result == 'success'){
               $scope.result = {"class":"alert-success","text":"Successfully registered! Please await your activation email!"};
            } else if(data.error != undefined) {
               $scope.result = {"class":"alert-error","text":data.error};
            }

         });
      }
   };
}

function ActivateCtrl($scope,$routeParams,$http){
    delete $http.defaults.headers.common['X-Requested-With'];
    $http.defaults.headers.post["Content-Type"] = "application/x-www-form-urlencoded";

    $http.post(server+'/json/activate',"key="+$routeParams.key).success(function(data) {
        $scope.returned = true;
        if(data.result == 'success'){
            $scope.result = {"class":"alert-success","text":"Account activated!"};
        } else {
            $scope.result = {"class":"alert-error","text":data.error};
        }
    });
}
