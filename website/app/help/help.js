
function HelpCtrl($scope, $modal, $http){
    $scope.openQuestion = function(id) {
        $http.get('/api/question/'+id.toString()).success(function (data) {
            $modal.open({
                templateUrl: '/app/help/question-modal.html',
                controller: QuestionModalController,
                resolve: {
                    question: function () {
                        return data;
                    }
                }
            });
        });
    };

    $http.get('/api/question?results_per_page=100').success(function (data) {
        $scope.questions = [];
        $.each(data.objects, function(k,v){
            if(v.answered !== false){
                $scope.questions.push(v);
            }
        });
    });
}

HelpCtrl.resolve = {
    lang: function($translate, $translatePartialLoader, $q){
        $translatePartialLoader.addPart('help');
        return $translate.refresh();
    }
};
